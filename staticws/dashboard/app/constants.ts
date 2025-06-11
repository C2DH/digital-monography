export const endpoint = "https://20cks5gkc3.execute-api.eu-west-1.amazonaws.com";

export const getGitBranch = function (): string {
    return "test";
    // NOTE: this is correct, restore
    // if (process.env.NEXT_PUBLIC_GIT_BRANCH === undefined) {
    //     return "develop";
    // } else {
    //     return process.env.NEXT_PUBLIC_GIT_BRANCH;
    // }
}
