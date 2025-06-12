'use client'

import { useEffect, useState } from 'react';
import TnbBookCard from "./_components/TnbBookCard";
import { API_ENDPOINT, API_STAGE } from "./constants";
import { IBook, getAlert } from "../types/books";

export default function Home() {
  // TODO: fetch the correct available books data
  // TODO: read the alert
  const [books, setBooks] = useState<IBook[]>([
    {
      authors: "Pawel Kaminski",
      slug: "guidelines-for-drafting-manuscripts",
      title: "Guidelines for Drafting Manuscripts",
      alert: getAlert(""),
    },
  ]);
  useEffect(() => {
    // require("bootstrap/dist/js/bootstrap.bundle.min.js");
    async function fetchStatusData() {
      try {
        const resp = await fetch(`${API_ENDPOINT}/${API_STAGE}/alerts`);
        const json = await resp.json();
        console.log("json", json);
        // const preSignedUrl = preSignedUrljson["presigned_url"];
        // const resp = await fetch(preSignedUrl);
        // const json = await resp.json();
      } catch (e) {
        console.error(e);
      }
    };
    // fetchStatusData();
  }, []);
  return (
    <div className="container">
      <h1 className="mt-5">Manuscripts available</h1>
      <div className="d-flex flex-column flex-md-row p-4 gap-4 py-md-5 align-items-center justify-content-center">
        <div className="list-group">
          {books.map((book) => (
            <TnbBookCard
              authors={book.authors}
              slug={book.slug}
              key={book.slug}
              title={book.title}
              alert={book.alert}
            ></TnbBookCard>)
          )}
        </div>
      </div>
    </div>
  );
}
