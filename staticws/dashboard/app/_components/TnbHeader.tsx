import Link from 'next/link'; // otherwise error https://nextjs.org/docs/messages/no-html-link-for-pages
import { API_ENDPOINT, API_STAGE, DBX_ENDPOINT } from "./../constants";

export default function TnbHeader() {
    return (
        <header>
            <nav className="navbar navbar-expand-md navbar-dark fixed-top bg-dark">
                <div className="container-fluid">
                    <img src="favicon.ico" alt="icon-with-notebook-and-pen"></img>
                    <Link className="navbar-brand" href="/">Dashboard for Living Books</Link>
                    <button
                        className="navbar-toggler" type="button"
                        data-toggle="collapse" data-target="#navbarCollapse"
                        aria-controls="navbarCollapse" aria-expanded="false"
                        aria-label="Toggle navigation">
                        <span className="navbar-toggler-icon"></span>
                    </button>
                    <div className="collapse navbar-collapse" id="navbarCollapse">
                        <ul className="navbar-nav mr-auto">
                            <li className="nav-item active">
                                <a className="nav-link"
                                    target="_blank" rel="noopener noreferrer"
                                    href={DBX_ENDPOINT}
                                >Dropbox</a>
                            </li>
                            <li className="nav-item">
                                <a className="nav-link"
                                    href={`${API_ENDPOINT}/${API_STAGE}/login`}
                                // href="https://20cks5gkc3.execute-api.eu-west-1.amazonaws.com/test/login"
                                >Login</a>
                            </li>
                        </ul>
                    </div>
                </div>
            </nav>
        </header>
    )
}
