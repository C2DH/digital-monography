export type Person = {
    firstName: string,
    lastName: string,
    age: number,
    visits: number,
    progress: number,
    createdAt: Date,
    status: string,
    rank: number,
}

export type IAsset = {
    alttext: string
    author: string
    caption: string
    comments: string
    fp: string
    is_color: boolean | null
    is_on_paper: boolean
    is_ready: boolean
    location: string | null
    medium: string
    metadata_table: string
    pk: string
    slug: string
    source: string
    target: string
}

export type IRef = {
    pk: number // this probably should be string
    fn: string
    targetId: string
    text: string
    href: string
    prevString: string
    prevHref: string
    elem: string
    assetId: string | null
}

export type IS3Object = {
    keyEncoded: string,
    key: string,
    lastModified: string | undefined,
    size: number | undefined,
}
