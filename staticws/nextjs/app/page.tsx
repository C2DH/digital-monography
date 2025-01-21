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
                <div className="btn-toolbar mb-3" role="toolbar">
                  <div className="btn-group mr-2" role="group">
                    <button className="btn btn-primary disabled">
                      <svg width="15px" height="15px" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <g>
                          <path d="M20,16v4a2,2,0,0,1-2,2H4a2,2,0,0,1-2-2V6A2,2,0,0,1,4,4H8" fill="none" stroke="#FFFFFF" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" />
                          <polygon fill="none" points="12.5 15.8 22 6.2 17.8 2 8.3 11.5 8 16 12.5 15.8" stroke="#FFFFFF" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" />
                        </g>
                      </svg>
                    </button>
                    <a href={`https://www.dropbox.com/home/Aplikacje/drpb-upload-alert-test/${slug}`} className="btn btn-primary">Edit</a>
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
                  </div>
                </div>
                <div className="btn-group" role="group">
                  <div className="btn-toolbar mb-3" role="toolbar">
                    <div className="btn-group mr-2" role="group">
                      <button className="btn btn-primary disabled">
                        <svg width="17px" height="17px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M8 6H10V8H8V6Z" fill="#FFFFFF" />
                          <path d="M10 10H8V12H10V10Z" fill="#FFFFFF" />
                          <path d="M8 14H10V16H8V14Z" fill="#FFFFFF" />
                          <path d="M11.5 8H18V6.5H11.5V8Z" fill="#FFFFFF" />
                          <path d="M18 12H11.5V10.5H18V12Z" fill="#FFFFFF" />
                          <path d="M11.5 16H18V14.5H11.5V16Z" fill="#FFFFFF" />
                          <path fillRule="evenodd" clipRule="evenodd" d="M5 3H21V19H5V3ZM6.5 4.5H19.5V17.5H6.5V4.5Z" fill="#FFFFFF" />
                          <path d="M2 6V22H18V20.5H3.5V6H2Z" fill="#FFFFFF" />
                        </svg>
                      </button>
                      <a href={`https://github.com/digital-monographs/${slug}`} className="btn btn-outline-primary">Public source</a>
                      <a href={`https://github.com/digital-monographs/${slug}/issues`} className="btn btn-outline-primary">Discussion</a>
                      <a href={`https://cpy-dgtmon-dev-staticws-wip.s3.eu-west-1.amazonaws.com/read/${slug}/index.html`} className="btn btn-outline-primary">Digital</a>
                      <a href="" className="btn btn-outline-primary disabled">Paper</a>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </span>
        </div>
      </div>
    </div>
  );
}
