# Digital monography

Platform for scholars of digital humanities to publish their digital work.

## Documentation

[Notes and materials related with the project](https://uniluxembourg-my.sharepoint.com/:f:/r/personal/pawel_kaminski_uni_lu/Documents/Digital%20Monography%20Documents?csf=1&web=1&e=YYBKgk) can be found on the University's OneDrive shared directory. Access to the directory is given upon request. Some of other important project documents include:
* [Jira board](https://degruyter.atlassian.net/jira/software/projects/TNB/boards/59);
* [concept document](https://docs.google.com/document/d/1-iBdDUBQe8O8vU5hF83HuAKAacU7xEpgUfpdi975-CM/edit?exids=71471482,71471477&tab=t.0);
* [notes from meetings related to the project](https://uniluxembourg-my.sharepoint.com/:f:/r/personal/pawel_kaminski_uni_lu/Documents/Digital%20Monography%20Documents/Meeting%20Notes?csf=1&web=1&e=Mbc9E9);
* [notes from workshop of 7th December 2023](https://docs.google.com/document/d/1DniLbpg7pNBygPI1s-L6i6DjEW4tjvXVBhYtyFm1wyg/edit?tab=t.0);
* [author's guidelines for drafting manuscripts](https://cpy-dgtmon-dev-staticws-wip.s3.eu-west-1.amazonaws.com/read/guidelines-for-drafting-manuscripts/index.html).

The development cycle is based on release cycles 4 months each. The direction of development is coordinated with project's partners during monthly meetings.

## CI/CD pipeline status

| Branch  | Status                                                                                                                                                                                                                     |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| main    | [![pipeline status](https://gitlab.com/uniluxembourg/c2dh/private/degruyter/digital-monography/badges/main/pipeline.svg)](https://gitlab.com/uniluxembourg/c2dh/private/degruyter/digital-monography/-/commits/main)       |
| develop | [![pipeline status](https://gitlab.com/uniluxembourg/c2dh/private/degruyter/digital-monography/badges/develop/pipeline.svg)](https://gitlab.com/uniluxembourg/c2dh/private/degruyter/digital-monography/-/commits/develop) |

## Design principles

* Sustainability is the highest priority of this project. Books should be hosted as static web pages without a need for dedicated servers. When possible, websites related to the project, like the reader or the dashboard, should not require any application logic on the server-side after web pages are built.
* The functionality of the code should be guessable just by looking at `src/<microservice>/main.py` module. The details of implementing this functionality can be hidden in other modules in this microservice.
* Code shared between microservices should be writen and stored in `src/_common/<filename>.py` files and copied to the microservices that use it with a command specified in the `Makefile` file.
* The state of the pipeline (state resulting from processing a manuscript) should be shared using the "metadata" object. For example, if you want to pass some information from the Preparer microservice to the Builder Microservice, you should store it in appropriate record in `metadata.DocumentMetadata` in Preparer and load from this object in Builder. Metadata is saved in multiple places for conveniance, e.g. in the database, as json files in the file storage shared between microservices and as json in `<scripts>` tag in html.
* Rely on features of MS Word for `.docx` input, JupyterLab/Notebook for `.ipynb` input and on JupyterBook/Sphinx-doc for output as much as possible.
* Target MyST specification rather that bespoke solutions.
* The deployment is steered by the `git push` command ran in the develop or master branches. Note however that the code of the microservices is pulled by the infrastructure from the docker image repository, so the developer has to point to the proper version number in `.versions.json` and push an image tagged with this version before the CI/CD pipeline tries to pull the image from the repo.

## Architecture design

### Architecture overview

The project consists of the following main software components.

| Name                                                        | Layer  | Description                                                                                                                                                             |
| ----------------------------------------------------------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [pipeline](src/)                                            | BL     | Microservices that process input manuscript, verify it, and build output for other apps to use. The pipeline includes multiple micro services that are described below. |
| [mammoth](https://github.com/kaminski-pawel/python-mammoth) | BL     | Python library for transforming `.docx` into markdown.                                                                                                                  |
| [CI/CD pipeline](./.gitlab-ci.yml)                          | DevOps | Set of scripts for applying changes to the infrastructure.                                                                                                              |
| [dashboard](staticws/dashboard/)                            | UI     | Dashboard with tools for authors and editors to help their work on the manuscript.                                                                                      |
| [reader](staticws/reader/)                                  | UI     | Copy of degruyter.com website to show how the digital books can be integrated with de Gruyter's platform.                                                               |

![architecture_abstract](./arch_abstract.svg)

_Image repo_ is the docker image repository from where the CI/CD pipeline pulls a specific microservice code.

The main workflow for generating digital monographies can be simplified as an interaction between the dropbox, entrypoint, preparer, verifier and builder microservices.

![simplified_diagram_digital_book](./cartoon-book-digital.png)

The workflow for generating docx for typesetting is not yet implemented. The most work here is made by the wordprocessor triggered by the endpoint microservice.

![simplified_diagram_paper_book](./cartoon-book-paper.png)

### Details of pipeline architecture

![aws_architecture_diagram](./arch_details.svg)

For the full architecture see [the instructions on generating an infrastrucutre visualisation](#generating-infrastrucutre-visualisation) and open the produced `graphviz.html` file.

The architecture attempts to follow the pattern of `... -> s3 upload -> Lambda invoke -> s3 upload -> ...`. Sometimes an upload to s3 can and should invoke multiple Lambda functions. It can be also advantageous to have an SQS queue as a part of the chain. This allows for a modular design, which brings some benefits with it.

The platform consists of the following microservices (Lambda functions):
| Name              | In VPC? | Description                                                                  |
| ----------------- | ------- | ---------------------------------------------------------------------------- |
| **entrypoint**    | false   | Exposes REST endpoints, incl. OAuth and webhooks to integrate with Dropbox.  |
| **dropbox**       | false   | Calls Dropbox API to retrieve files from Dropbox and writes them to s3.      |
| **preparer**      | true    | Does all the transformations of the files in the author package.             |
| **verifier**      | true    | Checks the author package against the verification rules.                    |
| **github**        | false   | Pushes the processed documents to GitHub remote repository.                  |
| **builder**       | true    | Runs Jupyter Book to build a book out of processed documents.                |
| **gpu**           | false   | Generates pre-signed url from private S3 bucket.                             |
| **wordprocessor** | false   | Transforms docx files for the paper version.                                 |

Deployment of each microservice should be done in order:

| Order | Stage name  | Command | Description |
| ----- | ----------- | ------- | ----------- |
| 1     | **version** | `vim .versions.json`        | In `.versions.json` appropriately increment _latest_ and _stable_ version numbers of a microservice you've made changes to in the `src/<microservice>` dir |
| 2     | **apply**   | `git push`                  | As you push your changes to GitLab, the CI/CD pipeline is run, including deployment of changes to the infrastructure; if the image version has changed in the `.versions.json`, the Docker container will be updated on the cloud |
| 3     | **build**   | `make <microservice>/build` | Builds Docker image |
| 4     | **tag**     | `make <microservice>/tag`   | Tags the image with a tag specified in `.versions.json` |
| 5     | **push**    | `make <microservice>/push`  | Pushes the image to docker registry (remember to login to the registry with `make login`) |

`make <microservice>/push` is a useful alias for builing, tagging and pushing a particular microservice. Note that there is a **race condition** - docker container has to be built, tagged and pushed before the apply stage pulls the image from registry. If CI/CD pipeline job fails with error `Source image <registry>/<image>:<tag> does not exist. Provide a valid source image.` re-run that job. Make sure that you had built, tagged and pushed the image in question.

### Details of each microservice architecture

Every microservice consists of:
* Dockerfile
* requirements.txt
* main.py
and optionally other files with implementation details.

`lambda_handler()` function in each `src/<microservice>/main.py` file is an entrypoint to this microservice. Data about the event that triggered this microservice and context in which this microservice is being run are passed as arguments to `lambda_handler(event, context)`.

The `lambda_handler()` should call abstract wrapper subprocedures, which call concrete subprocedures with the actual logic.

#### Wrapper subprocedures

The main role of wrapper subprocedures is to add logging and audit trails to each call of concrete subprocedures.

```py
try:
    from actual_business_logic import concrete_subprocedure
except (ImportError, ModuleNotFoundError):
    from .actual_business_logic import concrete_subprocedure  # type: ignore

def _wrapper_subprocedure(*args, **kwargs) -> t.Any:
    try:
        res = concrete_subprocedure(*args, **kwargs)
        logger.info(
            f"Response from concrete_subprocedure: {json.dumps(res, default=str)}"
        )
        return res
    except Exception as e:
        logger.exception(
            f"Log message. Error: {repr(e)}"
        )
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Audit trail message.",
        )
        raise
```

#### Concrete subprocedures

Concrete subprocedures hide implementation details. Those subprocedures should be located in separate files and not in the main file.

Code common to more than one microservice should be written in the `src/_common/<module_name.py>` and copied from there to the microservices using `make copy/<module_name>` command.

### Multiple environments

The project has two cloud environments: main and develop. Each time you run `git push` on the "develop" branch, you  trigger the CI/CD for the "develop" environment. Similarly, when you accept the merge request to the "main" branch, the CI/CD for the "main" branch will be invoked.

### Naming convention

#### Infrastructure

Each resource deployed should follow the same naming convention: `<project>-<env>-<awsservice>-<microservice>-<details>`

* `project` should be always "dgtmon". Helpful e.g. when you look for a IAM Policy related to the project - just start typing the name of the project and you'll filter only relavant items.
* `env` is generally the name of the environment ("main" or "develop"). For shared resources (e.g. ECR images) and for legacy resources it can be equal to "dev".
* `awsservice` is the abbreviation of a infrastructure resource. It should anwser the question: "what is it".
* `microservice` is the related service, like "builder" or "preparer". `microservice` can also be "general" or "gen" if the resource is for general use. You can also leave it empty.

For example, the full name of a resource could be
`dgtmon-main-s3-verifier-logs-warning`.

It is highly recommended to define `<awsservice>-<microservice>-<details>` as Terraform variable in `infra/variables.tf` file. The value has to be then filled in the `secrets/encrypted.tfvars.json` using the "sops" tool.

Then, when defining resources in the `.tf` files use variables:
```tf
resource "aws_awsservice_awsresource" "some_name" {
  name = "${var.project}-${var.env}-${var.some_name_set_in_variables}"
}
```

## Local development

You can check the basic workflow of the platform by running local scripts. To do that, follow these steps:

1. Start the container in the background.

```sh
make dev/start
```

1. Test the basic workflow.

```sh
make dev/test
```

0. Build a Jupyter Book out of a manuscript stored in a `data/input` directory. Replace `slug-of-your-manuscript` with the name of this directory.

```sh
make dev/draft SLUG="slug-of-your-manuscript"
```

Please keep in mind that the local script uses only part of the actual workflow. Consider testing on the cloud instead.

You can also try to execute the scripts directly through your CLI:

```sh
python scripts/prepare_and_build.py book_path="/mnt/c/Users/Pawel.kaminski/OneDrive - University of Luxembourg/Books/examples"
```

## Dependencies

Python version is defined in `.python-version`. Python dependencies are described in `requirements.txt` files both per-service in `src/<service-name>` and in testing environment at the root of the project. Beyond that the project requires:

* docker
* git
* sops
* make
* terraform (if you want to use the tf cli outside of the gitlab-ci pipeline)

## Updating code

Images are hosted in the Docker Hub registry as well as in the Amazon Elastic Container Registry (ECR). When applying changes in the terraform configuration, AWS will pull images from ECR, build and deploy them using the tags specified in the `.versions.json` file. Note that the main environment will use stable version as the container tag whereas other environments will use the latest version number.

In order to push images to the Docker Hub and to ECR, you first have to login to the registry. Note that the `Makefile` exposes common commands for building, tagging and pushing important docker images. We strongly advise using the `Makefile` commands. For example when you made some changes to the Preparer Lambda code, you can push them using the following commands.

```sh
# Update the lastest version of the preparer image
vim .versions.json
# Login to Docker Hub
make login
# Build the preparer image
make preparer/build
# Tag the preparer image with the tag specified as lastest in the .versions.json file
make preparer/tag
# Push docker image to the docker registry
make preparer/push
```

Note that pushing the image to the docker registry itself will not update the code deployed to the AWS infrastructure. For that you need to trigger the CI/CD pipeline, for example by pushing `.versions.json` code to the main or the develop branch.

See `Makefile` and `.gitlab-ci.yml` for details.

## Updating infrastructure configuration

Changes to the Terraform Infrastructure as Code will be updated automatically after push to `main` and `develop` branches.

See `.gitlab-ci.yml` for details.

## Encrypting secret files

To encrypt a file, use the sops tool.

```sh
sops -e secrets/dev.tfvars.json > secrets/dev.tfvars.enc.json
```

To set up sops, you can follow the [official instructions](https://github.com/getsops/sops) or [unofficials guides](https://dev.to/stack-labs/manage-your-secrets-in-git-with-sops-g0a).

## Setup the infrastructure

Steps to configure the platform on your own AWS account.

### Configure an Identity Provider in AWS IAM

Configure GitLab as an identity provider for IAM. This will allow IAM to recognize GitLab as a trusted entity that we can assign permissions via an IAM Role.
Navigate to IAM in the AWS Management Console, and then click on "Identity Providers" on the sidebar under "Access Management". After that, click on the button saying "Add provider" on the top right-hand side.

Make sure that the option for OpenID Connect is selected on the top, this is because OpenID Connect allows you to configure trust relationships with third party accounts including but not limited to GitLab. Also ensure that the provider URL is GitLab's root URL, https://gitlab.com as well as the Audience. The provider URL is the URL from which the OpenID configuration is obtained. See [this walkthrough](https://community.aws/content/2dquEzIKfm2wVH77AYmApToZdWj/gitlab-with-terraform) for details.

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

See the `secrets/` dir to find policies examples to attach to that IAM Role.

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

When adding a new Lambda function (a new microservice), please follow these steps:
1. Add the microservice code to the `src/ ` directory.
1. Add the test code to the `tests/ ` directory.
1. Copy and modify one of the `.tf` files to define a Lambda function. Usually you can reuse all of the IaC code changing only the `<old-function-name>` to `<new-function-name>`.
1. Update the `Makefile`.
1. Update the `.versions.json`.
1. Update the `secrets/encrypted.tfvars.json` (remember to use the `sops` tool) and `variables.tf`.
1. Push the git repository to remote
1. Build, tag and push the new image to the container registry (see `Makefile`).
1. Retry the GitLab job.

## Linting and type checking

### Type cheching

To run type check use `make typecheck` function. You can also run `mypy src/<microservice>/` to run the type checker directly on a given microservice.

At the beginning of the project every microservice was type checked and linted. However, the beginning of the project was also packed with tight deadlines and so type checking and linting ceased to be a priority. Below is the table with the type check implementation status. Note that a support for type check could be easily implemented for microservices marked with a star "*".

| Name          | Implemented? | 
| ------------- | ------------ | 
| entrypoint    | true         | 
| dropbox       | false*       | 
| preparer      | false        | 
| verifier      | false        | 
| github        | false*       | 
| builder       | false        | 
| gpu           | true         | 
| wordprocessor | true         | 

### Linting

We use flake8 for linting. Run `flake8 src/<microservice>/` to run the linting script. 

## Further developments

### Schema-based database vs. schema-less database

Currently, the architecture stores data important for the dashboard in a DynamoDB. DynamoDB is a serverless, noSQL, key-value database. Most importantly, we treat it as a schema-less database. This is both a strengh and a weakness. This approach was chosen instead of a schema-based database (like PostgreSQL, MySQL or SQLite) because of specificity of handling manuscripts. Commonly, web applications use schema-based databases for storing their state. When someone changes content of a web app, the state is written to a database and displayed from the database to users.

Contrarily, the state in a document transformation software is stored in documents themselves. It is the documents that are being processed that are the source of the truth. We don't control what users do in a separate document processing software like Microsoft Word or Jupyter Lab. We see the changes only when the document is uploaded to our software. We cannot use any of common "diff" algorithms to track changes, because the diffing solutions are usually based on longest common subsequence algorithms (e.g. on Myers' diffing algorithm). Those work great on a source code, markdown or even json, but they are not meant for a complex XML files underlying even the simplest MS Word file. Therefore it is non-trivial task to maintain consistency between different versions of the same document (what if part of a document is moved to another document? what if a document is renamed and modified?). For this reasons I decided to use the uploaded manuscripts as a single source of truth. When a user uploads a document, all database records relating to this document are emptied and the software creates from scratch new db records.

I see this as a controversial choice and I encourage to keep looking for a better alternative.

#### Pros of schema-less db

* Serverless solutions are super cheap. Databases like PostgreSQL require servers, which makes them more costly.
* DynamoDB is fully managed, there is no need for maintenance. Even with managed database solutions there is usually a need for managing backups, making updates, etc. This is not the case with DynamoDB.

#### Cons of schema-less db

* When the software changes (e.g. the dashboard or the preparation of db records) the schema in which the data is stored changes as well. It is up to the client of this data to parse it correctly. With schema-based sql databases there is usually some migration mechanism to synchronize the changes in the schema. With the current solution, the changes apply only to the documents uploaded after the change. In case of db records written before the change and after the change you will have to write logic to remodel the data after those items are retrieved. This logic has to be written in the client that receives the data (e.g. in the dashboard).

### Migration to Jupyter Book v2

Jupyter Book is a series of open-source workflows and code that anyone can use to build a “living,” digital textbook. It is the software that we use for building a static website out of manuscripts.

The project was made with Jupyter Book v1 (further refered to as "JB1" or "v1"), which adds Jupyter Notebook integration to the [Sphinx documentation generator](https://github.com/sphinx-doc/sphinx). With time, the maintainers devoted more and more time to Jupyter Book v2 (further "JB2" or "v2"). JB2 is a complete re-write of the project, so migration from JB1 to JB2 is a non-trivial task. Please see below few of my thought about migration to v2.

#### Clarification on the naming

It is difficult to express this issue in part due to unclear naming. Few definitions to clarify:

| Name | Description |
| ---- | ----------- |
| MyST | Extension of markdown syntax. Made by Executable Book Project, made for handling features useful for books, like references, footnotes, admonitions, glossaries, etc. |
| MyST.md (mystmd or myst.md) | Software of similar purpose as JupyterBook v1 (similar functionalities) but written in TypeScript. Works well with hosting services sold by Curvenote Inc. |
| myst-cli | npm package for MyST.md |
| mystjs | Development fork of MyST.md created by Curvenote Inc. |

Also, it is imporant to understand the difference between Jupyter Notebook and Jupyter Book.

| Name | Description |
| ---- | ----------- |
| Jupyter Notebook | Jupyter Notebook can colloquially refer to two different concepts, either the user-facing application to edit code and text (this is the editor you edit your code in), or the underlying file format which is interoperable across many implementations (".ipynb" files). |
| Jupyter Book | Open-source tool for building publication-quality books from MyST markdown files and .ipynb files. |

#### Background

JB2 and mystmd are being developed mainly by contributors from two companies: [Curvenote](https://curvenote.com/) and [2i2c](https://2i2c.org/). To quote the [documentation](https://web.archive.org/web/20250219074454/https://mystmd.org/guide/deployment): “MyST was designed to be deployed as an application” with MyST server underneath and not as a static site with microservices underneath (which is how our book project is made). “At present, only Curvenote provides out-of-the-box support for deployment of MyST websites”. As a result, I found it difficult to use JB2 to build static websites that would work on AWS S3.

#### Problems with migration to JB2

##### Python vs TypeScript

First, it is important to note the JB2 is just a thin wrapper around myst.md, which is written in TypeScript. I see 2 ways to use both Python and TypeScript in the `builder` microservice:
* use Python+TS Docker container,
* split the `builder` into multiple microservices, e.g. `pre-builder` (Python), `builder` (TS) and `post-builder` (Python).

##### Static websites with JB2

When built with `myst build --html` the output cannot be simply uploaded to S3 as a static website. This would result in `TypeError: Cannot read properties of undefined (reading 'handle')` error. Without deeper research this seems like a chunking error (JB2 uses [esbuild](https://esbuild.github.io/api/#splitting) for chunking), which could indicate some deeper issues.

To work properly, the build output needs to be served with [Vercel's serve repo](https://github.com/vercel/serve), e.g. `npx serve _build/html`. This creates a need of some compute capabilities behind static websites, which S3 does not have. A solution may be to use one of the providers that supports this solution, for example:
* [Netlify](https://mystmd.org/guide/deployment-netlify),
* [GitHub Pages](https://mystmd.org/guide/deployment-github-pages).

An alternative solution might be to fork myst.md and try to replace all features that require a server with neutral ones.

<!-- 1. install node.js v 20
1. npm install mystmd
1. myst build --html
1. create myst.yml config file (different from v1)
1. copy _build/html to s3 bucket -->

### Additional change suggestions

* add e2e cloud testing on actual Lambdas
* mypy type checking
* flake8 linting
* refactor link management (refs.py)
* migrate JupyterBook v1 to v2
* restore verification rules
* deploy wordprocessor and connect with others
* dashboard should fetch book details and alert info from API (now hard coded)

## Sundry

### Generating infrastrucutre visualisation

To generate a visualization of an infrastructure as defined by .tf IaC files follow these steps:

1. Copy current project directory so that you don't have to migrate state nor reconfigure. E.g. `cp digital-monography tfgraph`.
1. Initalize terraform locally with `terraform init`.
1. Run `terraform graph`.
1. Copy output from terraform graph command to [WebGraphViz](http://www.webgraphviz.com/?tab=map) and select on "Generate Graph".
1. Save the `<div id="graphviz_svg_div">` tag as "graphviz.html" in the root of the project.

### Changing guidelines github repo 

One way to upload changes to the guidelines repository is to clone the github remote repo to your local machine, apply your update and push your changes. You can use the following command to point to the ssh private key that is used by github user.

```sh
git config --add --local core.sshCommand 'ssh -i ~/.ssh/filename'
```

### Updating PGP keys with GPG

If the gpg library fails with a message `gpg: signing failed: No secret key`, the likely reason is expiration of the pgp key. To update pgp key used in CI/CD pipeline, use gpg library following these steps:

```
gpg --list-keys
gpg --edit-key [keyId]
> expire
> save
> quit
gpg --armor --export-secret-keys [keyId] > sth.txt
```

In GitLab, update "CI/CD Settings" > "Variables" > "PGP_KEY" with the new private pgp key.

### Accessing project email

Please consult the internal documentation in the [c2dh backstage](https://c2dh.atlassian.net/wiki/spaces/DDRI/pages/162923897/Related+links) for more details about accessing and managing the emails connected with the project.
