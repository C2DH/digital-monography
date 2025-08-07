import { Context, APIGatewayEvent } from 'aws-lambda';

/*
* Why is this microservice written in TypeScript?
* I couldn't use the same pattern as the other microservices because jupyter-book v1 and v2
* deployed in the same environment would cause a conflict of dependencies.
* I could have used Python as with other microservices, but jupyter-book v2 is just a wrapper around 
* TypeScript npm libraries, especially `myst-cli` and `mystmd`.
* (see https://github.com/jupyter-book/jupyter-book/blob/v2.0.0b2/py/jupyter_book/__main__.py)
*/
export const lambda_handler = async (event: APIGatewayEvent, context: Context) => {
    return {
        statusCode: 200,
        body: JSON.stringify({
            message: 'Hello from Lambda!',
            input: event,
        }),
    };
};
