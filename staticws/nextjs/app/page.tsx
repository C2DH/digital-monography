'use client'

import Link from 'next/link';
// import "./_styles/treeView.css";

export default function Home() {
  // useEffect(() => {
  //   require("bootstrap/dist/js/bootstrap.bundle.min.js");
  // }, []);
  const slug = "guidelines-for-drafting-manuscripts";
  return (
    <div className="container">
      <h1 className="mt-5">Manuscripts available</h1>
      <div className="d-flex flex-column flex-md-row p-4 gap-4 py-md-5 align-items-center justify-content-center">
        <div className="list-group">
          <span className="list-group-item list-group-item-action d-flex gap-3 py-3">
            <img src="favicon.ico" alt="twbs" width="32" height="32" className="rounded-circle flex-shrink-0"></img>
            <div className="d-flex gap-2 w-100 justify-content-between">
              <div>
                <h6 className="mb-0">Guidelines for Drafting Manuscripts</h6>
                <p className="mb-0 opacity-75">Pawel Kaminski</p>
                <div className="btn-group" role="group">
                  <a href={`https://www.dropbox.com/home/Aplikacje/drpb-upload-alert-test/${slug}`} className="btn btn-outline-primary">Folder</a>
                  <a href={`https://github.com/digital-monographs/${slug}`} className="btn btn-outline-primary">GitHub</a>
                  <a href={`https://github.com/digital-monographs/${slug}/issues`} className="btn btn-outline-primary">Issues</a>
                  <Link href={{
                    pathname: '/headings',
                    query: { slug: slug },
                  }} className="btn btn-outline-primary">
                    Headings
                  </Link>
                  <Link href={{
                    pathname: '/events',
                    query: { slug: slug },
                  }} className="btn btn-outline-primary">
                    Events
                  </Link>
                  <Link href={{
                    pathname: '/assets',
                    query: { slug: slug },
                  }} className="btn btn-outline-primary">
                    Assets
                  </Link>
                  <Link href={{
                    pathname: '/citations',
                    query: { slug: slug },
                  }} className="btn btn-outline-primary">
                    Citations
                  </Link>
                  <Link href={{
                    pathname: '/warnings-groups',
                    query: { slug: slug },
                  }} className="btn btn-outline-primary">
                    Warnings
                  </Link>
                  <a href={`https://cpy-dgtmon-dev-staticws-wip.s3.eu-west-1.amazonaws.com/read/${slug}/index.html`} className="btn btn-outline-primary">Digital</a>
                  <a href="" className="btn btn-outline-primary disabled">Paper</a>
                </div>
              </div>
            </div>
          </span>
        </div>
      </div>
    </div>
  );
}
