# **Pelican launch on Azure cloud services**

### **OVERVIEW**
Datametica intends to bring its suite of products starting with the Pelican Data Verification product to the cloud marketplace. We have implemented support to launch and use Pelican over Kubernetes and can be integrated with Azure's AKS service

### **DIRECTORY STRUCTURE**

```
├── chart
│   └── pelican     <-- Pelican helm charts to deploy on AKS
├── deploy          <-- ARM template to create AKS infra for Pelican deployment
├── README.md
└── resources       
```

### **DEPLOYMENT ARCHITECTURE**

![](resources/pelican-azure-ref-arch.png)

Pelican integrates well with AKS as show in above achitecture diagram and accelerates the data validation process between source and destination data bases and performs automated data validations.

Kubernetes manages Pelican single-instance solutions and the Pelican UI endpoints by default exposed externally using a LoadBalancer Service on a single port 8080 - for HTTP interface. The MySQL DB is exposing the service on port 3306 internally to pelican POD.

The sizing and configuration can be customized and managed using ConfigMaps and Helm chart values.yml

## **INSTALLATION**

### Steps for running Pelican(BYOL) on AKS:

In order to deploy Pelican, we will require an AKS cluster. We can use an existing cluster or create a new one. Steps for creating a new cluster are as given below:

#### Setting up an AKS cluster

1\. In order to interact with Azure using command line, we will have to use Azure cloud shell or install az-cli package on our local system. 

Refer below provided link to download Azure CLI on local system:

**https://docs.microsoft.com/en-us/cli/azure/install-azure-cli**

2\. Login into your azure account using command if using AZ CLI on local system:

```sh
az login
```

3\. If you have multiple Azure subscriptions, set the desired subscription to run the application using following command:

```sh 
az account set --subscription [SubscriptionID/SubscriptionName]
```

4\. Clone the git repository to the environment you are using for setup:

```sh
git clone [git_url]
```

5\. Change the directory to switch to the “pelican” directory in the cloned repository. Provide appropriate virtual networking details in the "**azuredeploy.parameters.json**" file under "**deploy**" directory. You can either use an existing vnet or create a new one by changing the value of parameter “**virtualNetworkNewOrExisting**” to either “**existing**” or “**new**”. 

6\. Finally, Run the below command to set up AKS cluster:

```sh
az deployment group create --name [DeploymentName] --resource-group [ResourceGroupName] --template-file deploy/azuredeploy.json --parameters deploy/azuredeploy.parameters.json
```


#### **Note** 
****
Please provide the deployment and an existing resource-group name in the above command. In case you need to access any internal applications or databases, please use the resource group with Azure VPN setup in order to let Pelican communicate with internal applications.
****

Above steps will ensure that you have a new AKS Cluster to deploy the pelican application.
&nbsp;
&nbsp;
#### Steps for deploying Pelican application on AKS cluster using Helm Charts:

In order to deploy Pelican using Helm charts, we will require docker images packaging the application. To get the images, we will need to subscribe to the Azure Marketplace Offer for Pelican. Below are the steps for same:

1\. Go to Azure portal and search for Azure Marketplace.

2\. Search for "Pelican" in "Data Analytics" section or directly search for “Pelican” in Azure Marketplace.

3\. Click on "**Get it now**" or "**Purchase**".

4\. Provide the necessary details asked in the UI.

Once the offer subscription is successful, you will be able to see the docker images in the defined container registry in the offer.
#### **Note** 
****
This is a BYOL solution which requires a valid license to use. You are responsible for purchasing and managing your own licenses from Datametica. Request a license https://www.datametica.com/contact-us/ or sales.pelican@datametica.com
****
&nbsp;
##### Updating Helm charts:
&nbsp;
Now edit the “**values.yaml**” file present in the Helm charts in “**chart**” directory of cloned git repo.

Provide the image repo name and tag in the “**image**” section under container name **pelican** in the Helm charts using the images provided by the Azure Pelican offer subscription.

For example:

```sh
pelican:
  replicas: 1
  image:
    repo: "sampleRegistry.azurecr.io/datameticasolutionsprivatelimited1595414718157/pelican-byol/pelican"
    tag: "latest"
  namespace: "default"
```
&nbsp;
Provide the image repo name and tag in the “**image**” section under container name **pelicandb** in the Helm charts using the image built by the Dockerfile for DB image. The DB image should also be hosted in the same container registry as pelican image else it would require creation and configuration of additional kubernetes secrets for pulling image from another private registry. 

Reference configuration:

```sh
pelicandb:
  replicas: 1
  image:
    repo: "sampleRegistry.azurecr.io/pelicandb"
    tag: "latest"
  port: 3306
  service:
    annotations: {}
    type: ClusterIP
    targetPort: 3306
  password: "SomeStrongPassword"
```
The **password** field in last line of above configuration is for setting the password that will be used for **pelicanuser** for mysql database configuration.

MySQL will also require a root password to be set by default in order to start up and do necessary configurations and changes to the database. Therefore, provide the MySQL root password under **templates** section in the **charts** directory in the **pelicandb-statefulset.yaml** file. 

Reference configuration:

```sh
    spec:
      containers:
      - name: pelican-db
        image: "{{ .Values.pelicandb.image.repo }}:{{ .Values.pelicandb.image.tag }}"
        imagePullPolicy: Always
        env:
          - name: MYSQL_ROOT_PASSWORD
            value: YOUR_PASSWORD_HERE
```
 
&nbsp;
 
Then, provide the value for “**loadBalancerSourceRanges**” in the helm charts under “**service**” section.

The value of the field should be any subnet range from which the application should be accessible.

**For example:** “52.63.11.82/32”.

It can also be set to “0.0.0.0/0” to allow all inbound traffic on the load-balancer listener port.

Finally run the following commands in “pelican” directory of cloned git repository on the CLI to deploy the application:

```sh
 az aks get-credentials --resource-group [ResourceGroupName] --name [cluster-name];
```

```sh
kubectl create secret docker-registry acr-secret --namespace default --docker-server=[ContainerRegistryName].azurecr.io --docker-username=[RegistryAdminUsername] --docker-password=[RegistryAdminPassword]
```
```sh
helm install pelican chart/
```
&nbsp;
#### **Note**

****

The secret should be created in same environment from where the helm charts will be deployed.

Container Registry admin username and password needs to be enabled and are found under “Access Keys” setting in the Container Registry.

**[cluster-name]** will be the name of AKS cluster in which application is to be deployed. In case of new cluster creation using ARM template in current git repo, the cluster name will be: **Pelican-cluster**.
****

The above commands will successfully install the Pelican application on the mentioned cluster.
&nbsp;
&nbsp;
## Accessing Pelican Application UI

1\. On Azure portal, open the Azure cloud shell.

2\. Enter the below commands:

```sh
az aks get-credentials --resource-group [resource-group-name] --name [cluster-name];
```
```sh
kubectl get svc
```
After running the above command, you will get the LoadBalancer IP address and port number to launch the Pelican application from a web browser with appropriate network configurations (in case of VPN).

