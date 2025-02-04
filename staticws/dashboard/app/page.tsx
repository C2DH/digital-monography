'use client'

import Link from 'next/link';
import TnbBookNav from "./_components/TnbBookNav";

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
                <p className="mb-2 opacity-75">Pawel Kaminski</p>
                <TnbBookNav slug={slug} color="primary"></TnbBookNav>
                <div className="btn-toolbar mb-3" role="toolbar">
                  <div className="btn-group mr-2" role="group">
                    <button className="btn btn-primary disabled">
                      <svg width="20px" height="20px" fill="#FFFFFF" viewBox="0 0 1920 1920" xmlns="http://www.w3.org/2000/svg" transform="matrix(-1, 0, 0, 1, 0, 0)" stroke="#FFFFFF" strokeWidth="50.0">
                        <g>
                          <path d="m0 1016.081 409.186 409.073 79.85-79.736-272.867-272.979h1136.415V959.611H216.169l272.866-272.866-79.85-79.85L0 1016.082ZM1465.592 305.32l315.445 315.445h-315.445V305.32Zm402.184 242.372-329.224-329.11C1507.042 187.07 1463.334 169 1418.835 169h-743.83v677.647h112.94V281.941h564.706v451.765h451.765v903.53H787.946V1185.47H675.003v564.705h1242.353V667.522c0-44.498-18.07-88.207-49.581-119.83Z"></path>
                        </g>
                      </svg>
                    </button>
                    <a  
                        target="_blank" rel="noopener noreferrer" 
                        href={`https://github.com/digital-monographs/${slug}`}
                        className="btn btn-outline-primary"
                      >Public source</a>
                    <a  
                        target="_blank" rel="noopener noreferrer" 
                        href={`https://github.com/digital-monographs/${slug}/issues`}
                        className="btn btn-outline-primary"
                      >Discussion</a>
                    <a  
                        target="_blank" rel="noopener noreferrer" 
                        href={`https://cpy-dgtmon-dev-staticws-wip.s3.eu-west-1.amazonaws.com/read/${slug}/index.html`}
                        className="btn btn-outline-primary"
                      >Digital</a>
                    <a href="" className="btn btn-outline-primary disabled">Paper</a>
                    <a href="" className="btn btn-outline-primary disabled">Zip package</a>
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
