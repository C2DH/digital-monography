# Development

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

## Linting and type checking

### Type cheching

To run type check use `make typecheck` function. You can also run `mypy src/<service>/` to run the type checker directly on a given service.

At the beginning of the project every service was type checked and linted. However, the beginning of the project was also packed with tight deadlines and so type checking and linting ceased to be a priority. Below is the table with the type check implementation status. Note that a support for type check could be easily implemented for services marked with a star "*".

| Name          | Implemented? | 
| ------------- | ------------ | 
| entrypoint    | true         | 
| dahsboard     | false*       | 
| dropbox       | false*       | 
| preparer      | false        | 
| verifier      | false        | 
| github        | false*       | 
| builder       | false        | 
| gpu           | true         | 
| orm           | true         | 
| wordprocessor | broken       | 

### Linting

We use flake8 for linting. Run `flake8 src/<service>/` to run the linting script. 

## Database migrations

We use alembic as the database migration system.

```sh
# create a db revision (migration) file
alembic revision -m "Create account table"
# run upgrade operations to HEAD
# alternative 1: alembic upgrade ae1027a6acf
# alternative 2: alembic upgrade +2
alembic upgrade head
# view migration history
alembic history --verbose
```

## Troubleshooting

### I uploaded a book to Dropbox but I don't see the output nor the logs

If you uploaded a book to Dropbox but you don't see the output nor the logs, it probably means that you didn't authenticate the app with Dropbox before uploading. Be sure to hit the "login" button in the dashboard before uploading manuscript to Dropbox.

## Sundry

### How do references and targets work?

#### Preparer

Preparer iterates over anchor tags, registering Ref and Target objects. It also registeres RefTarget model, which is a bridge for linking potentially multiple Ref instances to a Target. Refs, Targets and RefTargets are stored in a state (in a table), not yet linked with each other.
For each unique target, place target label above referenced content.

#### Downstream

Unlike preparer, builder and wordprocessor have access not only to a current chapter, but to a whole book. First, update numbering of the targets, respectively ommiting paper_only and digital_only targets. Secondly, update refs, making sure they have a href attribute linking to the correct target instance and that number in their text will match number of the related target. Thirdly, replace placeholders with updated values.

It is advised that builder and wordprocessor work in a similar way.

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
