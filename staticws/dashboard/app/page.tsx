'use client'

import Link from 'next/link';
import TnbBookCard from "./_components/TnbBookCard";

export default function Home() {
  // useEffect(() => {
  //   require("bootstrap/dist/js/bootstrap.bundle.min.js");
  // }, []);
  const manuscripts = [
    {
      authors: "Pawel Kaminski",
      slug: "guidelines-for-drafting-manuscripts",
      title: "Guidelines for Drafting Manuscripts",
    },
    {
      authors: "Anita Lucchesi",
      slug: "sample-chapter",
      title: "For a new hermeneutics of practice in digital public history (snippet)",
    },
  ];
  return (
    <div className="container">
      <h1 className="mt-5">Manuscripts available</h1>
      <div className="d-flex flex-column flex-md-row p-4 gap-4 py-md-5 align-items-center justify-content-center">
        <div className="list-group">
          {manuscripts.map((book) => (
            <TnbBookCard
              authors={book.authors}
              slug={book.slug}
              key={book.slug}    
              title={book.title}
            ></TnbBookCard>)
          )}
        </div>
      </div>
    </div>
  );
}
