'use client'

import { useEffect, useState } from 'react';
import TnbBookCard from "./_components/TnbBookCard";

type IBook = {
  authors: string,
  slug: string,
  title: string,
  alert: string,
}

export default function Home() {
  const endpoint = "https://20cks5gkc3.execute-api.eu-west-1.amazonaws.com";
  const [books, setBooks] = useState<IBook[]>([
    {
      authors: "Pawel Kaminski",
      slug: "guidelines-for-drafting-manuscripts",
      title: "Guidelines for Drafting Manuscripts",
      alert: "",
    },
    {
      authors: "Anita Lucchesi",
      slug: "hermeneutics-of-practice",
      title: "For a new hermeneutics of practice in digital public history",
      alert: "",
    }
  ]);
  useEffect(() => {
    // require("bootstrap/dist/js/bootstrap.bundle.min.js");
    console.log("test");
    async function fetchStatusData() {
      try {
        const resp = await fetch(`${endpoint}/test/alerts`);
        const json = await resp.json();
        console.log("json", json);
        // const preSignedUrl = preSignedUrljson["presigned_url"];
        // const resp = await fetch(preSignedUrl);
        // const json = await resp.json();
      } catch (e) {
        console.error(e);
      }
    };
    fetchStatusData();
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
