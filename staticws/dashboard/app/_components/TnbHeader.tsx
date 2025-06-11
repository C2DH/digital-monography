import Link from 'next/link'; // otherwise error https://nextjs.org/docs/messages/no-html-link-for-pages
import { endpoint, getGitBranch } from "./../constants";

export default function TnbHeader() {
    const stage = getGitBranch();
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
                                    href="https://www.dropbox.com/home/Aplikacje/drpb-upload-alert-test"
                                >Dropbox</a>
                            </li>
                            <li className="nav-item">
                                <a className="nav-link"
                                    href={`${endpoint}/${stage}/login`}
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
