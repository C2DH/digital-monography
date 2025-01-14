'use client'

// import "./_styles/treeView.css";

export default function Home() {
  // useEffect(() => {
  //   require("bootstrap/dist/js/bootstrap.bundle.min.js");
  // }, []);

  return (
    <div>
      <main>
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
                    <div className="btn-group" role="group" aria-label="Basic outlined example">
                      <a href="https://www.dropbox.com/home/Aplikacje/drpb-upload-alert-test/guidelines-for-drafting-manuscripts" className="btn btn-outline-primary">Folder</a>
                      <a href="https://cpy-dgtmon-dev-staticws-wip.s3.eu-west-1.amazonaws.com/read/guidelines-for-drafting-manuscripts/index.html" className="btn btn-outline-primary">Output</a>
                      <a href="/headings?slug=guidelines-for-drafting-manuscripts" className="btn btn-outline-primary">Headings</a>
                      <a href="/events?slug=guidelines-for-drafting-manuscripts" className="btn btn-outline-primary">Events</a>
                      <a href="/assets?slug=guidelines-for-drafting-manuscripts" className="btn btn-outline-primary">Assets</a>
                      <a href="/citations?slug=guidelines-for-drafting-manuscripts" className="btn btn-outline-primary">Citations</a>
                      <a href="/warnings-groups?slug=guidelines-for-drafting-manuscripts" className="btn btn-outline-primary">Warnings</a>
                    </div>
                  </div>
                </div>
              </span>
            </div>
          </div>

        </div>
      </main>
      {/* <div className="d-flex 
  justify-content-center align-items-center">
        <button
          type="button"
          className="btn btn-primary"
          data-bs-toggle="modal"
          data-bs-target="#exampleModal"
        >
          Launch demo modal
        </button>

        <div
          className="modal fade"
          id="exampleModal"
          tabIndex="-1"
          aria-labelledby="exampleModalLabel"
          aria-hidden="true"
        >
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title" id="exampleModalLabel">
                  Modal title
                </h5>
                <button
                  type="button"
                  className="btn-close"
                  data-bs-dismiss="modal"
                  aria-label="Close"
                ></button>
              </div>
              <div className="modal-body">...</div>
            </div>
          </div>
        </div>
      </div> */}
    </div>
  );
}
