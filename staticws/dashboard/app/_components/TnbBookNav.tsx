import Link from 'next/link';

export default function TnbBookNav({ slug, color }: { slug: string, color: string }) {
    return (
        <div className="btn-toolbar mb-1" role="toolbar">
            <div className="btn-group mr-2" role="group">
                <button className={`btn btn-${color} disabled`}>
                    <svg width="20px" height="20px" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <g>
                            <path d="M20,16v4a2,2,0,0,1-2,2H4a2,2,0,0,1-2-2V6A2,2,0,0,1,4,4H8" fill="none" stroke="#FFFFFF" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
                            <polygon fill="none" points="12.5 15.8 22 6.2 17.8 2 8.3 11.5 8 16 12.5 15.8" stroke="#FFFFFF" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
                        </g>
                    </svg>
                </button>
                <a
                    href={`https://www.dropbox.com/home/Aplikacje/drpb-upload-alert-test/${slug}`}
                    className={`btn btn-${color}`}
                >Edit</a>
                <Link href={{
                    pathname: '/headings',
                    query: { slug: slug },
                }} className={`btn btn-outline-${color}`}>
                    Headings
                </Link>
                <Link href={{
                    pathname: '/events',
                    query: { slug: slug },
                }} className={`btn btn-outline-${color}`}>
                    Events
                </Link>
                <Link href={{
                    pathname: '/warnings-groups',
                    query: { slug: slug },
                }} className={`btn btn-outline-${color}`}>
                    Warnings
                </Link>
                <Link href={{
                    pathname: '/citations',
                    query: { slug: slug },
                }} className={`btn btn-outline-${color}`}>
                    Citations
                </Link>
                <Link href={{
                    pathname: '/assets',
                    query: { slug: slug },
                }} className={`btn btn-outline-${color}`}>
                    Assets
                </Link>
            </div>
        </div>
    )
}
