# Infrastructure setup

## Steps to configure infrastructure

Steps to configure the platform on your own AWS account.

### Adding a new AWS account

The project supports multi-environment deployment. For the IaC scripts to work, every environment should have its own AWS account. If you want to deploy this project on your infrastructure just treat it as a new environment. To set up a new environment, follow these instructions:
1. [Create a new AWS account](https://aws.amazon.com/resources/create-account/) or connect to an existing one.
1. Using the root user, create a new AWS account and copy the number of the new account to encrypted tfvars in `secrets/` dir.
1. In the IAM Identity Center, navigate to a multi-account permission and assign users/groups to the new account with applicable permission sets.
1. Be sure to wait some time for the AWS staff to verify the new account.

### Configure an Identity Provider in AWS IAM

In this step you will configure GitLab as an identity provider for IAM. This will allow IAM to recognize GitLab as a trusted entity that we can assign permissions via an IAM Role.
First, navigate to IAM in the AWS Management Console, and then click on "Identity Providers" on the sidebar under "Access Management". After that, click on the button saying "Add provider" on the top right-hand side.

Make sure that the option for OpenID Connect is selected on the top, this is because OpenID Connect allows you to configure trust relationships with third party accounts including but not limited to GitLab. Also ensure that the provider URL is GitLab's root URL, https://gitlab.com, as well as the Audience. The provider URL is the URL from which the OpenID configuration is obtained. See [this walkthrough](https://community.aws/content/2dquEzIKfm2wVH77AYmApToZdWj/gitlab-with-terraform) for details.

### Create an IAM Role for GitLab CI

Click on "Roles" under "Access Management" in the IAM page and then click on the "Create role" button on the top right of the page to create IAM Role that the CI/CD pipeline can assume. The following IAM Roles are needed:
* for deployment
* for post-deployment (e.g. for publishing static websites to deployed resources)

The trusted entity type should be "web identity". In the "Trust relationships" settings, edit the condition in the trust policy to something like this:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::<AWS_ACCOUNT_ID>:oidc-provider/gitlab.com"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringLike": {
                    "gitlab.com:sub": [
                        "project_path:<PATH_TO_THE_REPO>:ref_type:branch:ref:main",
                        "project_path:<PATH_TO_THE_REPO>:ref_type:branch:ref:develop"

                    ]
                }
            }
        }
    ]
}
```

See the `secrets/` directory to find policies examples to attach to those IAM Roles.

### Create terraform state backend

Head over to the S3 page in the AWS Console and click "Create bucket" on the right side. Give the bucket a globally unique name.

Update the "bucket" field file "terraform.backend" in the `main.tf` file with the name of the new bucket.

### Create state lock table

Create a DynamoDB Table, we can visit the DynamoDB page on the AWS Console, and click on "Create table" on the right side of the page. Make sure it is done in the same region as the S3 bucket. Call the Partition Key "LockID" and set it to be a string. I recommend choosing the On-demand plan and add appropriate tags. We can leave the rest as the default settings and click on "Create table".

Update the "dynamodb_table" field file "terraform.backend" in the `main.tf` file with the name of the new table.

The `main.tf` can look something like:

```
terraform {
  backend "s3" {
    bucket         = "[NAME_OF_STATE_BACKEND_BUCKET]"
    dynamodb_table = "[NAME_OF_STATE_LOCK_TABLE]"
    encrypt        = true
    profile        = "oidc"
  }
}

provider "aws" {
  profile = "oidc"
  region  = var.region
}
```

### Store secrets

Some secrets used in the project require extra level of protection. To manage them, create AWS Secrets Manager and store an "other type of secret". Make sure that the tfvar matches the name of the infrastructure resource.

### Add variables to GitLab repository

Go to the home page of the GitLab repository, and click on "CI/CD" under the "Settings" dropdown menu on the very bottom of the sidebar. Then click "Expand" on the "Variables" section and click on "Add variable". Have the Key equal DGTMON_ROLE_*_ARN as defined in `.gitlab-ci.yml` and the value be the ARN of the Role created in the step above. Remember to select the option "Protect variable".

Also, add the "AWS_DEFAULT_REGION" variable with value equal to the AWS region selected for the above mentioned resources.

## Configure the infrastructure after initial deployment

There are additional steps you have to perform to complete setting up the infrastructure.

### Allow IAM Users to push to ECR registries in other environments

Every environment should be deployed in its own AWS account. For simplicity, a single IAM User should be able to perform actions on ECR registries among all accounts, like "ecr:PutImage". For the purposes of ECR access, the IAM User is defined in the "develop" environment and ECR Repository Policies have to be added in other environments that should be affected by that IAM User.
Follow the steps below to set up the needed cross-account permissions to the non-develop AWS accounts: First, navigate to "ECR" > "Features & Settings" > "Permissions" and hit "Edit" button. Then, generate a statement similar to the one in `secrets/policy_ecr_crossaccount.json`. Remember to add ARN of cli-IAM Users to ECR in the "Principal" field. Also, replace placeholders with appropriate AWS account ids. The images will not be copied automatically (there is no "pull through cache" configured), so you might need to push the latest ones.

### Register webhooks endpoints

After API Gateway was created, you can connect the deployed infrastructure with the Dropbox via webhooks. In order to set up the webhooks integration, be sure to register the "Redirect URI" and "Webhook URI" in the [Dropbox dashboard](https://www.dropbox.com/developers/apps?_tk=pilot_lp&_ad=topbar4&_camp=myapps).
* The "Redirect URI" should match `<api_agw_endpoint_develop>/<stage>/oauth_callback`.
* The "Webhook URI" should match `<api_agw_endpoint_develop>/<stage>/webhook`.
See details of the endpoints in `src/entrypoiny/main.py`.

## Adding access to the infrastructure to a new user

### Create a IAM User for terminal access

Remember, the platform makes updates by pulling docker images from the ECR container repository. In order to update the source code, users should push their modifications to the repository using docker (preferably via commands defined in the `Makefile` file).

To add a CLI client for a specific user the admin should add an IAM User directly in `infra/users.tf` and attach it to a group with ECR permissions. Name of the new user should be written in the encrypted `secrets/variables.tf` file. Push changes via git to "main" or "develop" branch.

Every user pushing to the ECR must have installed on their machines:
* docker (tested on Docker v24.0.6)
* aws-cli (tested on 2.15.25)
The user should also have login and password to the Docker Hub.
When installing or configuring aws-cli, the user should add AWS access key and secret access key of the IAM User created in the previous step. The `~/.aws/credentials` and `~/.aws/config` files should now include those keys (not necessarily as "default"):

```
[default]
aws_access_key_id = <YOUR_AWS_ACCESS_KEY>
aws_secret_access_key = <YOUR_AWS_SECRET_ACCESS_KEY>
```

```
[default]
region = eu-central-1
output = json
```

In the future, consider replacing access keys with AWS CLI v2 to enable authentication through a user in IAM Identity Center. See [docs](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sso.html) for more details.

### Create a user to access the AWS console

The root profile has to navigate to the IAM Identity Center (it has to be enabled first with "Identity Center directory" as its identity source) and select "Add user". Username has to be "Lastname_Firstname". Attach the new user to the "Developers" IAM Group. 
Make sure that the "Developers" IAM Group has "ReadOnlyAccess" or "ViewOnlyAccess" permission set assigned to it.

At this point the new user should be prompted to add a new password. The user should be able to finalize the creation by following the steps provided by the AWS. Particularly, the user should register a MFA device.

## Adding new Dropbox app

To create an app, set its options and/or see its details, navigate to Dropbox [dashboard](https://www.dropbox.com/developers/apps?_tk=pilot_lp&_ad=topbar4&_camp=myapps).

## Adding new Lambda function

When adding a new Lambda function (a new service), please follow these steps:
1. Add the service code to the `src/ ` directory.
1. Add the test code to the `tests/ ` directory.
1. Copy and modify one of the `.tf` files to define a Lambda function. Usually you can reuse all of the IaC code changing only the `<old-function-name>` to `<new-function-name>`.
1. Update the `Makefile`.
1. Update the `.versions.json`.
1. Update the `secrets/encrypted.tfvars.json` (remember to use the `sops` tool) and `variables.tf`.
1. Push the git repository to remote
1. Build, tag and push the new image to the container registry (see `Makefile`).
1. Retry the GitLab job.
