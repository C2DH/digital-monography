import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";

const s3Client = new S3Client({ region: "eu-central-1" });

async function uploadToS3(bucketName, key, body) {
    try {
        const command = new PutObjectCommand({
            Bucket: bucketName,
            Key: key,
            Body: body,
        });
        const response = await s3Client.send(command);
        console.log("Upload successful:", response);
    } catch (error) {
        console.error("Error uploading to S3:", error);
    }
}

describe("home page", () => {
    // before(() => {
    //     uploadToS3(Cypress.env('S3_APKG_UPLOAD'), 'test.md', 'Test, test.');
    // });

    it('should fetch APP_API_URL from .env file', () => {
        const apiUrl = Cypress.env('APP_API_URL');
        expect(apiUrl).to.equal('http://localhost:8000/api');
    });

    it('should fetch REACT_APP_API_URL from .env file', () => {
        const apiUrl = Cypress.env('REACT_APP_API_URL');
        expect(apiUrl).to.equal('http://localhost:8000/api/react/');
    });

    it('should fetch CYPRESS_HOME from .env file', () => {
        const appEnv = Cypress.env('CYPRESS_HOME');
        expect(appEnv).to.equal('index.html');
    });

    it('should fetch HOME from .env file', () => {
        const appEnv = Cypress.env('HOME');
        expect(appEnv).to.equal('index.html');
    });

    it('should fetch CYPRESS_S3_APKG_UPLOAD from .env file', () => {
        const appEnv = Cypress.env('CYPRESS_S3_APKG_UPLOAD');
        expect(appEnv).to.equal('test_bucket');
    });

    it('should fetch CYPRESS_BASE_URL from .env file', () => {
        const appEnv = Cypress.env('CYPRESS_BASE_URL');
        expect(appEnv).to.equal('dashboard url');
    });

})
