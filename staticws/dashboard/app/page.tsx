'use client'

import { useEffect, useState } from 'react';
import TnbBookCard from "./_components/TnbBookCard";
import { endpoint, getGitBranch } from "./constants";

type IAlert = {
  id: "" | "auth-rejected" | "verif-warning" | "pipeline-fail",
  icon: "" | "❌" | "⚠",
  color: "success" | "danger" | "warning",
  heading: string,
  message: string,
}

type IBook = {
  authors: string,
  slug: string,
  title: string,
  alert: IAlert,
}

function getAlert(alert: string): IAlert {
  if (alert == "auth-rejected") {
    return {
      id: alert,
      icon: "❌",
      color: "danger",
      heading: "Access denied. System rejected changes from unauthenticated user.",
      message: "The output will not show the latest version of the manuscript. Login in and reupload.",
    }
  } else if (alert == "verif-warning") {
    return {
      id: alert,
      icon: "⚠",
      color: "warning",
      heading: "System encountered serious issues with the manuscript.",
      message: 'We advise to navigate to the "Warnings" section and to fix them before continuing.',
    }
  } else if (alert == "pipeline-fail") {
    return {
      id: alert,
      icon: "❌",
      color: "danger",
      heading: "Processing the manuscript failed.",
      message: "The output might not show the latest version of the manuscript due to the error.",
    }
  } else {
    return {
      id: "",
      icon: "",
      color: "success",
      heading: "",
      message: "",
    }
  }
}

export default function Home() {
  // const endpoint = "https://20cks5gkc3.execute-api.eu-west-1.amazonaws.com";
  const stage = getGitBranch();
  console.log("stage", stage);
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
    console.log("test");
    async function fetchStatusData() {
      try {
        const resp = await fetch(`${endpoint}/${stage}/alerts`);
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
