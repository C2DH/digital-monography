'use client'

import { useState, useEffect } from 'react'

type InputData = {
  id: number, quote: string, author: string
};

export default function Page() {
  const [data, setData] = useState<InputData[]>([]);
  const [isLoading, setLoading] = useState(true);
  useEffect(() => {
    fetch("https://dummyjson.com/quotes/random/3")
      .then((res) => res.json())
      .then((data) => {
        console.log(">>data", data);
        setData(data);
        setLoading(false);
      })
  }, [])

  if (isLoading) return <p>Loading...</p>
  if (!data) return <p>No profile data</p>

  return (<div>
    <h1>Invoices Page</h1>
    {/* {data && <p>{JSON.stringify(data)}</p>} */}
    <ul>
      {data && data.map(({ id, quote, author }: InputData) => <li key={id}>* {quote} - {author}</li>)}
    </ul>

  </div>);
}
