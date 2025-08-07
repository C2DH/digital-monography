import { handler } from 'main';
import { APIGatewayEvent } from 'aws-lambda';

describe('Lambda Handler', () => {
    it('should return a 200 response', async () => {
        const event: APIGatewayEvent = {
            httpMethod: 'GET',
            path: '/',
            headers: {},
            multiValueHeaders: {},
            queryStringParameters: null,
            multiValueQueryStringParameters: null,
            pathParameters: null,
            stageVariables: null,
            requestContext: {} as any,
            body: null,
            isBase64Encoded: false,
        };

        const result = await handler(event, {} as any);
        expect(result.statusCode).toBe(200);
        expect(JSON.parse(result.body).message).toBe('Hello from Lambda!');
    });
});
