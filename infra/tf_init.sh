#!/bin/bash

# Global variables
secrets_path="$(dirname "$PWD")/secrets"
temp_secrets_path="$(dirname "$PWD")/secrets/secrets_tmp"

# itsm_aws_assume_role="arn:aws:iam::660616951977:role/Terraform_Developer"
itsm_aws_assume_role="arn:aws:iam::660616951977:role/CICD-admin-Access"

prerequisites=( jq glab )

##################### FUNCTIONS ###########################

    setup_glab(){
        GITLAB_REPO_URL="https://gitlab.com/gitlab-org/cli"
        RELEASES_API_URL="${GITLAB_REPO_URL}/-/releases.json"
        RELEASES_JSON=$(curl -s "${RELEASES_API_URL}")
        LATEST_VERSION=$(echo "${RELEASES_JSON}" | jq -r '.[0].name')
        DOWNLOAD_URL="${GITLAB_REPO_URL}/-/releases/${LATEST_VERSION}/downloads/glab_${LATEST_VERSION/v/}_Linux_x86_64.deb"
        echo
        echo "Downloading GitLab CLI ${LATEST_VERSION}_Linux_x86_64.deb ..."
        echo
        wget "${DOWNLOAD_URL}" -O "glab_${LATEST_VERSION}_Linux_x86_64.deb"
        sudo dpkg -i glab_"${LATEST_VERSION}"_Linux_x86_64.deb 
        glab auth login --hostname gitlab.com --token "$GITLAB_ACCESS_TOKEN"
    }

    # Check prerequisites 
    check_prereq(){
        for program in "${prerequisites[@]}" 
        do 
        if ! command -v "$program" &>/dev/null 
        then
            case "$program" in 

            glab)
            setup_glab
            ;;
                
            *)
            echo
            echo "Installing the '$program' program..."
            sudo apt -qqqq install -y "$program"
            ;;
            
            esac
        else 
        echo "Program $program already installed"     
        fi 
        done 
    }


    # Countdown function
    countdown() {
        local seconds="$1"
        tput civis # Hide cursor
        for ((i = $seconds; i > 0; i--)); do
            echo -ne "$i seconds left to resume this shell by hitting CTRL-C!\r"
            sleep 1
        done
        tput cnorm # Show cursor
        echo -e "\nWe are really exiting the shell in 5 seconds"
        sleep 5
        exit
    }

    # Check if the script is being directly executed or sourced
    if [ "$0" == "$BASH_SOURCE" ]; then
        echo "Please don't execute this script directly. Use '. $0' instead."
        echo
        echo "This script initializes a specific Terraform environment for a GitLab project."
        echo "It configures AWS and Terraform settings based on various criteria."
        echo "Prerequisites:"
        echo "- The script must be called with '. tf_init.sh', not './tf_init.sh'."
        echo "- Ensure necessary tools are installed: jq, sops, aws-cli, terraform, etc."
        echo "- Certain environment variables may need to be manually set, e.g., GL_USERNAME and GITLAB_ACCESS_TOKEN."
        echo "The script establishes an alias 'tf' for Terraform to ease the operations."
        countdown 10
    fi

    # Delete all temporary files after Exit
    cleanup_temp_files() {
        find "$temp_secrets_path"/ -type f -name "tmp.*" -exec rm {} \;
    }

    # Check git branch we're on and use the TEST statefile for branches other than MAIN
    set_statefile() {
        if [[ "$(git branch --show-current)" == "$(git symbolic-ref refs/remotes/origin/HEAD | awk -F'/' '{print $NF}')" ]]; then
            echo
            echo "---> !!! ATTENTION !!! <---"
            sleep 2
            echo "---> THIS IS THE MAIN BRANCH OF THE PROJECT <---"
            sleep 2
            echo "   We are using the LIVE Terraform statefile now. "
            STATE_NAME="live"
        else
            echo "We're not on the main branch."
            echo "We're using the TEST Terraform statefile now."
            STATE_NAME="test"
        fi
    }

    # Get the project ID with glab
    get_project_id() {
        glab api projects/:fullpath | jq -r .id
    }

    # Function for preparing sops
    sops_preparations() {
        # Step 1: Get the committer's email
        gpg_email="$(glab api user | jq -r .commit_email)"

        # Step 2: Search for all commits by this commit email
        commit_ids=($(glab api projects/:id/repository/commits?author="$gpg_email" | jq -r .[].id))

        # Initialize a variable to store the found key
        found_key=""

        # Step 3: Iterate through the array and check the signature for each commit
        for commit_id in "${commit_ids[@]}"; do
            signature=$(glab api projects/:id/repository/commits/"$commit_id"/signature | jq -r .gpg_key_primary_keyid)

            # Step 4: Compare the Short PGP Key with the Long PGP Key (Short Key in SOPS_PGP_FP)
            # Here, the Short Key is used for SOPS_PGP_FP
            export SOPS_PGP_FP="$(grep -n "$signature" "$(dirname "$PWD")/.sops.yaml" | awk -F':|,' '{print $2}' | tr -d "[:blank:]")"

            # If a GPG key is found, exit the loop
            if [ -n "$SOPS_PGP_FP" ]; then
                found_key="$SOPS_PGP_FP"
                break
            fi
        done

        # Step 5: Prepare all encrypted files to only be used with the found key
        # Find all files in the "secrets/" folder
        find "$secrets_path"/ -maxdepth 1 -type f | while read -r encrypted_file; do

            # Use the script to move the block with the desired fingerprint to the first position
            echo "Decrypting to temporary location: $encrypted_file"
            desired_fingerprint="$found_key"
            # Find the PGP block with fingerprint in the file
            block=$(jq --arg fingerprint "$desired_fingerprint" \
                '.sops.pgp[] | select(.fp == $fingerprint)' \
                "$encrypted_file")
            # Remove the found block from the file
            jq --arg fingerprint "$desired_fingerprint" \
                'del(.sops.pgp[] | select(.fp == $fingerprint))' \
                "$encrypted_file" >"$temp_secrets_path/temp.json" && mv "$temp_secrets_path/temp.json" "$encrypted_file"
            # Add the found block on top of the file
            jq --argjson block "$block" '.sops.pgp = [$block] + .sops.pgp' "$encrypted_file" >"$temp_secrets_path/temp2.json" && mv "$temp_secrets_path/temp2.json" "$encrypted_file"
        done
    }

    # Function for decrypting secrets
    sops_decrypt() {
        sops_preparations
        ## Decrypting Terraform Variables and create temp files to use
        secret_tmp="$(mktemp -p "$temp_secrets_path" --suffix .tmp.tfvars)"
        sops -d ../secrets/"$STATE_NAME".tfvars > "$secret_tmp"

        ## Decrypting AWS configuration
        aws_profile_tmp="$(mktemp -p "$temp_secrets_path" --suffix .tmp.aws_profile)"
        sops -d ../secrets/aws_cicd_profile_config > "$aws_profile_tmp"

        aws_cred_tmp="$(mktemp -p "$temp_secrets_path" --suffix .tmp.aws_cred)"
        sops -d ../secrets/aws_cicd_profile_credentials > "$aws_cred_tmp"
    }

    # Configure AWS Environment
    aws_configure() {
        export AWS_SHARED_SECRET_FILE="$aws_cred_tmp"
        export AWS_CONFIG_FILE="$aws_profile_tmp"
    }

    # Determine the AWS account based on tfvars "aws_account_environment"
    determine_aws_account() {
        echo
        echo "Attempting to determine the AWS account from the tfvars files..."
        echo
        det_aws_account="$(grep "aws_account_environment" "$secret_tmp" | awk -F'"' '{print $2}')"

        if [ -z "$det_aws_account" ]; then
            echo
            echo "No AWS account was found in the *aws_account_environment* variable."
        else
            echo
            echo "The *aws_account_environment* variable indicates that you are currently working in the following AWS account:"
            echo
            echo "AWS ACCOUNT: $det_aws_account"
        fi
    }

    # Set AWS Role based on AWS Account
    set_aws_role() {
        aws_configure
        determine_aws_account

        if [[ "$det_aws_account" == "delivery" ]]; then
            echo
            echo "We will work in the AWS DELIVERY account"
            sleep 1
            echo "Exporting the according Role now"
            export TF_VAR_assume_role_arn="$delivery_aws_assume_role"
            export AWS_PROFILE="DELIVERY"
            export AWS_DEFAULT_PROFILE="DELIVERY"
            eval $(
                aws sts assume-role --role-arn ${TF_VAR_assume_role_arn} --role-session-name "$USER"_DELIVERY --duration-seconds 21600 |
                    jq -r '.Credentials | "export AWS_ACCESS_KEY_ID=\(.AccessKeyId)\nexport AWS_SECRET_ACCESS_KEY=\(.SecretAccessKey)\nexport AWS_SESSION_TOKEN=\(.SessionToken)\n"'
            )
        elif [[ "$det_aws_account" == "itsm" ]]; then
            echo
            echo "We will work in the AWS DELIVERY account"
            sleep 1
            echo "Exporting the according Role now"
            export TF_VAR_assume_role_arn="$itsm_aws_assume_role"
            export AWS_PROFILE="ITSM"
            export AWS_DEFAULT_PROFILE="ITSM"
            eval $(
                aws sts assume-role --role-arn ${TF_VAR_assume_role_arn} --role-session-name "$USER"_ITSM --duration-seconds 21600 |
                    jq -r '.Credentials | "export AWS_ACCESS_KEY_ID=\(.AccessKeyId)\nexport AWS_SECRET_ACCESS_KEY=\(.SecretAccessKey)\nexport AWS_SESSION_TOKEN=\(.SessionToken)\n"'
            )
        else
            echo -e "\nNO AWS ACCOUNT FOUND\nPLEASE SETUP THE VARIABLE aws_account_environment\nin the <live> and <test> tfvar files\nin the folder secrets/ !\n"
            countdown 10
        fi
    }


##################### BODY ###########################
    clear
    trap 'cleanup_temp_files' EXIT INT
    echo
    echo "Welcome to the Terraform-GitLab Backend (TF_GL) initialization!"
    echo
    echo "WARNING: This shell session will be reconfigured to use a specific AWS Service Principal for the Git project's Terraform environment."
    sleep 1
    echo "For all other AWS interactions, please open and use a SEPARATE shell session!"
    echo "Proceed with caution."

    # Set Gitlab user and Token
    echo
    if [[ -z "$GL_USERNAME" ]]; then
        read -erp "Please enter your Gitlab username [e.g. wdegryuter]: " GL_USERNAME
    else
        echo "GL Username already set!"
        echo " Welcome $GL_USERNAME !"
        export GL_USERNAME="$GL_USERNAME"
    fi
    echo
    if [[ -z "$GITLAB_ACCESS_TOKEN" ]]; then
        read -erp "Please enter your Gitlab Personal Access Token: " GITLAB_ACCESS_TOKEN
        export GITLAB_ACCESS_TOKEN="$GITLAB_ACCESS_TOKEN"
    else
        echo "GL ACCESS TOKEN ALREADY SET"
    fi

    # Check Prerequisites
    check_prereq
    # Get Project ID
    PROJECT_ID="$(get_project_id)"
    ### Set TF State File
    set_statefile
    ### Starting init for specific project
    terraform init -reconfigure \
        -backend-config="address=https://gitlab.com/api/v4/projects/$PROJECT_ID/terraform/state/$STATE_NAME" \
        -backend-config="lock_address=https://gitlab.com/api/v4/projects/$PROJECT_ID/terraform/state/$STATE_NAME/lock" \
        -backend-config="unlock_address=https://gitlab.com/api/v4/projects/$PROJECT_ID/terraform/state/$STATE_NAME/lock" \
        -backend-config="username=$GL_USERNAME" \
        -backend-config="password=$GITLAB_ACCESS_TOKEN" \
        -backend-config="lock_method=POST" \
        -backend-config="unlock_method=DELETE" \
        -backend-config="retry_wait_min=5"
    ### Temporary Decryption of the according tfvars File
    sops_decrypt
    ### Set AWS Role based on AWS Account
    set_aws_role
    echo
    echo "We're set and ready to go!"
    echo
    echo "USE --> tf <---"
    echo "for APPLY and PLAN"
    echo "According to your git branch, we set the environment to"
    echo " --> $STATE_NAME <---"
    ### set alias Function for terraform
    tf() {
        command terraform "$1" -var-file="$secret_tmp" $2
    }
