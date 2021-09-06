"""
The following script is written in Python3 and is aimed at an interactive user choice based deployment of the application Pelican.

The script does the following functions:

1. Azure login and subscription selection
2. Launch a new AKS cluster or use an existing cluster
3. Pull the latest helm chart code from GitHub repository
4. Build Pelican db docker image and push to private Azure Container Registry
5. Connect to the AKS cluster and define docker credential to connect to private ACR using k8s secrets
6. Install Pelican application using the helm chart


In order to execute the script, run the following command:

    python3 deployment.py [--option argument]


Expected output:

    Successfully installed Pelican helm chart! You can now access Pelican UI by checking the LB endpoint using following command: kubectl get svc

"""

#!/usr/bin/python3

import subprocess
import sys
import os
import getpass
import argparse

if len(sys.argv) < 2:
    out = subprocess.getstatusoutput("python3 deployment.py -h")
    print("\n"+out[1])
    sys.exit()

my_parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, allow_abbrev=False,prog='createCluster',usage='python3 deployment.py [--option argument]',description='Subscribing the Pelican Application from Azure Marketplace',  epilog='Example Command: python3 deployment.py --username john.doe@microsoft.com  --git_url https://github.com/projects/AzureMarketplace.git  --subscriptionID 21e87802-e43e-4149-9921-90971c45638c  --resourcegroup Pelican_Product_RG --location EastUS --virtualNetworkNewOrExisting new --virtualNetworkName PelicanVnet --virtualNetworkAddressPrefix 172.26.10.0/24 --subnetName Pelican-Subnet --subnetAddressPrefix 172.26.10.0/25 --registryname sampleRegistry  --registryusername sampleRegistry  --registrypassword fehipfpwhhwphdqfphfwcjo  --loadbalancerrange 52.43.31.82/32 --dbpassword pelicanuser@123 --imagename sampleRegistry.azurecr.io/pelicanbyol --imagetag 1.0.1\n\n\n')
my_parser.add_argument('--username', action='store', help='Provide the Azure cloud username')
my_parser.add_argument('--git_url', action='store', help='Provide the Git URL for fetching Pelican Artifacts')
my_parser.add_argument('--subscriptionID', action='store', help='Provide the Azure subscription ID to use for the application deployment')
my_parser.add_argument('--resourcegroup', action='store', help='Provide the Azure resource group name to use for the application deployment')
my_parser.add_argument('--registryname', action='store', help='Provide the Azure Container Registry name used for Pelican offer subscription')
my_parser.add_argument('--registryusername', action='store', help='Provide the username for Azure Container Registry used for Pelican offer subscription')
my_parser.add_argument('--registrypassword', action='store', help='Provide the password for Azure Container Registry used for Pelican offer subscription')
my_parser.add_argument('--loadbalancerrange', action='store', help='Provide the Loadbalancer range to allow Pelican access to. Eg. 52.43.31.82/32')
my_parser.add_argument('--dbpassword', action='store', help='Provide the database password for pelican user')
my_parser.add_argument('--imagename', action='store', help='Provide the docker image URI provided by Pelican offer subscription')
my_parser.add_argument('--imagetag', action='store', help='Provide the docker image tag provided by Pelican offer subscription')
my_parser.add_argument('--virtualNetworkNewOrExisting', action='store', choices=['new','existing'], help='Confirm if new Vnet should be created or an existing should be used')
my_parser.add_argument('--virtualNetworkName', action='store', help='Provide the name of virtual network')
my_parser.add_argument('--virtualNetworkAddressPrefix', action='store', help='Provide the virtual network prefix')
my_parser.add_argument('--subnetAddressPrefix', action='store', help='Provide the subnet network prefix')
my_parser.add_argument('--subnetName', action='store', help='Provide the subnet name')
my_parser.add_argument('--location', action='store', help='Provide the location for virtual network (Check if desired location is not blocked)')


args = my_parser.parse_args()

if len(sys.argv) < 21:
    print("\nMissing arguments or argument values. \nPlease provide all the required arguments and values!!!\n")
    out = subprocess.getstatusoutput("python3 deployment.py -h")
    print(out[1])
    sys.exit()


username = args.username
git_url = args.git_url
SubscriptionID = args. subscriptionID
ResourceGroupName = args.resourcegroup
containerRegistryName = args.registryname
RegistryAdminUsername = args.registryusername
RegistryAdminPassword = args.registrypassword
loadBalancerSourceRanges = args.loadbalancerrange
DBpassword = args.dbpassword
imagename = args.imagename
imagetag = args.imagetag

out = subprocess.getstatusoutput("az --help")
if out[0] != 0:
    print("Azure cli does not exist!!!\n\n")
    print("Please install az-cli and run the script again.")
    sys.exit()


out = subprocess.getstatusoutput("docker --help")
if out[0] != 0:
    print("Docker tool does not exist!!!\n\nPlease install docker and run the script again.")
    sys.exit()


out = subprocess.getstatusoutput("helm --help")
if out[0] != 0:
    print("Helm utility does not exist!!!\n\nPlease install Helm and run the script again.")
    sys.exit()


out = subprocess.getstatusoutput("kubectl --help")
if out[0] != 0:
    print("Kubectl utility does not exist!!!\n\nPlease install kubectl and run the script again.")
    sys.exit()

password = getpass.getpass(prompt='Please enter your Azure account password:')

out = subprocess.getstatusoutput("az login -u {} -p {}".format(username, password))
if out[0] == 0:
    print("\nSuccessfully logged in into Azure Account!\n\n")
else:
    print("Failed to log in into Azure Account!\n\n"+out[1])
    sys.exit()


out = subprocess.getstatusoutput("az account set --subscription {}".format(SubscriptionID))
if out[0] == 0:
    print("Successfully switched to provided subscription!\n\n")
else:
    print("\nFailed to switch to provided subscription!\n\n"+out[1])
    sys.exit()


if str(os.path.exists('pelican')):
    out = subprocess.getstatusoutput("pwd")
    dir_path = "{}/pelican".format(out[1])
    os.chdir('pelican')
    out = subprocess.getstatusoutput("pwd")
    if out[1] == dir_path:
        print("Successfully switched to main directory: {}\n".format(dir_path))
    else:
        print("\nFailed to switch to main directory: {}\n\n".format(dir_path))
        sys.exit()
    print("\nPelican artifacts already exists...\n")
    choice = input("Want to pull latest version(y/n)?:")
    if choice != 'y' and choice != 'n':
        choice = input("\nInvalid input!!!\nPlease provide valid input(y/n):")
    if choice == 'y':
        out = os.system("git pull")
        if out == 0:
            print("\nSuccessfully pulled latest git repository for helm charts!\n")
        else:
            print("\nFailed to pull latest git repository for helm charts!\n\n"+str(out))
            sys.exit()
    elif choice == 'n':
        pass
    else:
        print("\nInvalid input!!!\nExiting.")
        sys.exit()


print("\nDo you want to deploy a new AKS cluster or use an existing one?\n")
choice = input("Please provide input (new/existing): ")
if choice == "new":
    clusterName = input("\nPlease provide the Pelican AKS cluster name: ")
    print("\nTrying to deploy a new Pelican AKS Cluster...\n")
    out = os.system("az deployment group create --name {} --resource-group {} --template-file deploy/azuredeploy.json --parameters deploy/azuredeploy.parameters.json --parameters resourceName={} --parameters VnetResourceGroup={} --parameters location={} --parameters virtualNetworkNewOrExisting={} --parameters virtualNetworkName={} --parameters virtualNetworkAddressPrefix={} --parameters subnetAddressPrefix={} --parameters subnetName={}".format(clusterName, ResourceGroupName, clusterName, ResourceGroupName, args.location, args.virtualNetworkNewOrExisting, args.virtualNetworkName, args.virtualNetworkAddressPrefix, args.subnetAddressPrefix, args.subnetName))
    if out == 0:
        print("\nSuccessfully deployed the Pelican AKS Cluster!\n")
    else:
        print("\nFailed to deploy Pelican AKS Cluster!\n\n"+str(out))
        sys.exit()
elif choice == "existing":
    clusterName = input("\nPlease provide the name of existing AKS cluster to deploy Pelican(Note: Make sure the cluster already exists and has necessary resources available to host the application):\n")
else:
    choice = input("\nPlease provide valid input (new/existing):")
    if choice == "new":
        clusterName = input("\nPlease provide the Pelican AKS cluster name: ")
        print("\nTrying to deploy a new Pelican AKS Cluster...\n")
        out = os.system("az deployment group create --name {} --resource-group {} --template-file deploy/azuredeploy.json --parameters deploy/azuredeploy.parameters.json --parameters resourceName={} --parameters VnetResourceGroup={} --parameters location={} --parameters virtualNetworkNewOrExisting={} --parameters virtualNetworkName={} --parameters virtualNetworkAddressPrefix={} --parameters subnetAddressPrefix={} --parameters subnetName={}".format(clusterName, ResourceGroupName, clusterName, ResourceGroupName, args.location, args.virtualNetworkNewOrExisting, args.virtualNetworkName, args.virtualNetworkAddressPrefix, args.subnetAddressPrefix, args.subnetName))
        if out == 0:
            print("\nSuccessfully deployed the Pelican AKS Cluster!\n")
        else:
            print("\nFailed to deploy Pelican AKS Cluster!\n\n"+str(out))
            sys.exit()
    elif choice == "existing":
        clusterName = input("\nPlease provide the name of existing AKS cluster to deploy Pelican(Note: Make sure it has necessary resources available to host the application):\n")
    else:
        print("\nInvalid input!!!\nExiting.")
        sys.exit()


choice = input("\nDo you want to build PelicanDB image?(y/n)")
if choice != 'y' and choice != 'n':
    choice = input("\nInvalid input!!!\nPlease provide valid input(y/n):")
if choice == 'y':
    out = os.system("docker build -t {}.azurecr.io/pelicandb:1.0.1 .".format(containerRegistryName))
    if out == 0:
        print("\nSuccessfully built the docker image!\n")
    else:
        print("\nFailed to build the docker image!\n\n"+str(out))
        subprocess.getstatusoutput("docker image rm -f {}.azurecr.io/pelicandb:1.0.1 && docker system prune -f".format(containerRegistryName))
        sys.exit()
elif choice == 'n':
    pass
else:
    print("\nInvalid input!!!\nExiting.")
    sys.exit()


choice = input("\nDo you want to push the PelicanDB image to private ACR?(y/n)")
if choice != 'y' and choice != 'n':
    choice = input("\nInvalid input!!!\nPlease provide valid input(y/n):")
if choice == 'y':
    out = subprocess.getstatusoutput("docker login {}.azurecr.io -u {} -p {} ".format(containerRegistryName, RegistryAdminUsername, RegistryAdminPassword))
    if out[0] == 0:
        print("Successfully logged in into the private docker registry!\n\n")
    else:
        print("\nFailed to login into the private docker registry!\n"+out[1])
        sys.exit()
    out = os.system("docker push {}.azurecr.io/pelicandb:1.0.1".format(containerRegistryName))
    if out == 0:
        print("\nSuccessfully pushed docker image into the private docker registry!\n\n")
    else:
        print("\nFailed to push docker image into the private docker registry!\n"+str(out))
        sys.exit()
elif choice == 'n':
    pass
else:
    print("\nInvalid input!!!\nExiting.")
    sys.exit()


out = os.system("az aks get-credentials --resource-group {} --name {}".format(ResourceGroupName, clusterName))
if out == 0:
    print("\nSuccessfully connected to the Pelican AKS Cluster!\n\n")
else:
    print("\nFailed to connect to the Pelican AKS Cluster!\n"+str(out))
    sys.exit()


out = subprocess.getstatusoutput("kubectl get secret | grep acr-secret")
if out[0] == 0:
    print("Kubernetes secret \"acr-secret\" for pulling docker images already exists. Please make sure the secret is configured correctly to pull images from private ACR!\n")
    choice = input("Do you want to recreate the secret?(y/n):")
    if choice != 'y' and choice != 'n':
        choice = input("\nInvalid input!!!\nPlease provide valid input(y/n):")
    if choice == 'y':
        out = subprocess.getstatusoutput("kubectl delete secret acr-secret")
        if out[0] == 0:
            print("\nSuccessfully deleted old Kubernetes secret for pulling images from private ACR!\n")
        else:
            print("\nFailed to delete old Kubernetes secret for pulling images from private ACR\n"+out[1])
            sys.exit()
        out = subprocess.getstatusoutput("kubectl create secret docker-registry acr-secret --namespace default --docker-server={}.azurecr.io --docker-username={} --docker-password={}".format(containerRegistryName, RegistryAdminUsername, RegistryAdminPassword))
        if out[0] == 0:
            print("\nSuccessfully created Kubernetes secret for pulling images from private ACR!\n")
        else:
            print("\nFailed to  create Kubernetes secret for pulling images from private ACR\n"+out[1])
            sys.exit()
    elif choice == 'n':
        pass
    else:
        print("\nInvalid input!!!\nExiting.")
        sys.exit()
else:
    out = subprocess.getstatusoutput("kubectl create secret docker-registry acr-secret --namespace default --docker-server={}.azurecr.io --docker-username={} --docker-password={}".format(containerRegistryName, RegistryAdminUsername, RegistryAdminPassword))
    if out[0] == 0:
        print("\nSuccessfully created Kubernetes secret for pulling images from private ACR!\n")
    else:
        print("\nFailed to  create Kubernetes secret for pulling images from private ACR\n"+out[1])
        sys.exit()


print("\n-------------------------------------------------------------------\n")
print("Helm chart deployment about to start...\n\nPlease make sure appropriate configurations have been done in helm charts as described in the documentation.")
print("\n-------------------------------------------------------------------\n")


choice = input("\nPlease confirm to initiate Helm chart deployment(y/n):")
if choice != 'y' and choice != 'n':
    choice = input("\nInvalid input!!!\nPlease provide valid input(y/n):")
if choice != 'y' and choice != 'n':
    print("\nInvalid input!!!\nExiting.")
    sys.exit()
if choice == 'y':
    out = subprocess.getstatusoutput("sleep 20; helm install --set-string pelican.service.loadBalancerSourceRanges={} --set-string pelicandb.password={} --set-string pelicandb.image.repo={}.azurecr.io/pelicandb --set-string pelican.image.repo={} --set-string pelican.image.tag={} {} chart/".format(loadBalancerSourceRanges, DBpassword, containerRegistryName, imagename, imagetag, clusterName.lower().replace("_", "")))
    if out[0] == 0:
        print("\nSuccessfully installed Pelican helm chart!\n\nYou can now access Pelican UI by using following URL:")
        out = subprocess.getstatusoutput("sleep 20 ; kubectl get services | grep LoadBalancer | awk '{{print $4;}}'")
        url = "http://{}:8080".format(out[1])
        print("\n\n\t\t{}\n\n".format(url))    
    else:
        print("\nFailed to install Pelican helm charts!\n"+out[1])
        choice = input("\nDo you want to clean up the previous version and retry?(y/n):")
        if choice == 'y':
            subprocess.getstatusoutput("helm uninstall {}".format(clusterName.lower().replace("_", "")))
            print("\nCleaned up the previous versions!\n\nAttempting to install new version...")
            out = subprocess.getstatusoutput("sleep 20; helm install --set-string pelican.service.loadBalancerSourceRanges={} --set-string pelicandb.password={} --set-string pelicandb.image.repo={}.azurecr.io/pelicandb --set-string pelican.image.repo={} --set-string pelican.image.tag={} {} chart/".format(loadBalancerSourceRanges, DBpassword, containerRegistryName, imagename, imagetag, clusterName.lower().replace("_", "")))
            if out[0] == 0:  
                print("\nSuccessfully installed Pelican helm chart!\n\nYou can now access Pelican UI by using following URL:")
                out = subprocess.getstatusoutput("sleep 20 ; kubectl get services | grep LoadBalancer | awk '{{print $4;}}'")
                url = "http://{}:8080".format(out[1])
                print("\n\n\t\t{}\n\n".format(url))
            else:
                print("\nFailed to install Pelican helm charts!\n"+out[1])
            sys.exit()
