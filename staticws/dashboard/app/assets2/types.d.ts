export type ITableRow = {
    pk: string
    fp: string
    location: string | null
    trunc_caption: string
    alttext: string
    is_color: boolean | null
    is_on_paper: boolean
    is_ready: boolean
    exists: bool | null
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
    asset_id: string | null
    elem: string
    fn: string
    href: string
    pk: string
    prev_href: string
    prev_string: string
    target_id: string
    text: string
}

export type IS3Object = {
    // keyEncoded: string,
    ETag: string,
    Key: string,
    LastModified: Date,
    Size: number | undefined,
    StorageClass: string,
}
