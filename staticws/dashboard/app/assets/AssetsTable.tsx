'use client'

import React from 'react';
import {
    Column,
    ColumnDef,
    ColumnFiltersState,
    flexRender,
    getCoreRowModel,
    getExpandedRowModel,
    getFacetedRowModel,
    getFacetedUniqueValues,
    getFilteredRowModel,
    getSortedRowModel,
    RowData,
    Row,
    SortingState,
    useReactTable,
    Updater,
} from '@tanstack/react-table';
import { IAsset, ITableRow, IRef, IS3Object } from "./types";

declare module '@tanstack/react-table' {
    //allows us to define custom properties for our columns
    interface ColumnMeta<TData extends RowData, TValue> {
        filterVariant?: 'text' | 'range' | 'select'
    }
}

export type TableProps<TData> = {
    data: TData[]
    columns: ColumnDef<TData>[]
    additionalData: { assetMetadata: IAsset[], refMetadata: IRef[], assetS3List: IS3Object[] }
    renderSubComponent: (props: { row: Row<TData>, assetMetadata: IAsset[], assetS3List: IS3Object[], refMetadata: IRef[] }) => React.ReactElement
    // getRowCanExpand?: (row: Row<TData>) => boolean
    columnFilters: ColumnFiltersState
    setColumnFilters: (updaterOrValue: Updater<ColumnFiltersState>) => void
    sorting: SortingState
    setSorting: (updaterOrValue: Updater<SortingState>) => void
}

export function Table({
    data,
    columns,
    additionalData,
    renderSubComponent,
    // getRowCanExpand,
    columnFilters,
    setColumnFilters,
    sorting,
    setSorting,
}: TableProps<ITableRow>): React.JSX.Element {
    const { assetMetadata, assetS3List, refMetadata } = additionalData;
    const table = useReactTable({
        columns,
        data,
        debugTable: true,
        debugHeaders: true,
        debugColumns: false,
        filterFns: {},
        getCoreRowModel: getCoreRowModel(),
        getExpandedRowModel: getExpandedRowModel(),
        getFacetedRowModel: getFacetedRowModel(),
        getFacetedUniqueValues: getFacetedUniqueValues(), // generate unique values for select filter/autocomplete
        getFilteredRowModel: getFilteredRowModel(), //client side filtering
        getRowCanExpand: () => true,
        getSortedRowModel: getSortedRowModel(), //client-side sorting
        onColumnFiltersChange: setColumnFilters,
        // onExpandedChange: () => { console.log("expanded") },
        onSortingChange: setSorting, //optionally control sorting state in your own scope for easy access
        // sortingFns: {
        //   sortStatusFn, //or provide our custom sorting function globally for all columns to be able to use
        // },
        //no need to pass pageCount or rowCount with client-side pagination as it is calculated automatically
        state: {
            columnFilters,
            sorting,
        },
        // autoResetPageIndex: false, // turn off page index reset when sorting or filtering - default on/true
        // enableMultiSort: false, //Don't allow shift key to sort multiple columns - default on/true
        // enableSorting: false, // - default on/true
        // enableSortingRemoval: false, //Don't allow - default on/true
        // isMultiSortEvent: (e) => true, //Make all clicks multi-sort - default requires `shift` key
        // maxMultiSortColCount: 3, // only allow 3 columns to be sorted at once - default is Infinity
    })
    return (<>
        <table className="table table-striped table-bordered">
            <thead>
                {table.getHeaderGroups().map(headerGroup => (
                    <tr key={headerGroup.id}>
                        {headerGroup.headers.map(header => {
                            return (
                                <th key={header.id} colSpan={header.colSpan}>
                                    {header.isPlaceholder ? null : (
                                        <>
                                            <div
                                                {...{
                                                    className: header.column.getCanSort()
                                                        ? 'cursor-pointer select-none'
                                                        : '',
                                                    onClick: header.column.getToggleSortingHandler(),
                                                }}
                                            >
                                                {flexRender(
                                                    header.column.columnDef.header,
                                                    header.getContext()
                                                )}
                                                {{
                                                    asc: ' 🔼',
                                                    desc: ' 🔽',
                                                }[header.column.getIsSorted() as string] ?? null}
                                            </div>
                                            {header.column.getCanFilter() ? (
                                                <div>
                                                    <Filter column={header.column} />
                                                </div>
                                            ) : null}
                                        </>
                                    )}
                                </th>
                            )
                        })}
                    </tr>
                ))}
            </thead>
            <tbody>
                {table.getRowModel().rows.map(row => {
                    return (
                        <React.Fragment key={row.id}>
                            <tr>
                                {row.getVisibleCells().map(cell => {
                                    return (
                                        <td key={cell.id}>
                                            {flexRender(
                                                cell.column.columnDef.cell,
                                                cell.getContext()
                                            )}
                                        </td>
                                    )
                                })}
                            </tr>
                            {/* row details */}
                            {row.getIsExpanded() && (
                                <tr>
                                    <td colSpan={row.getVisibleCells().length}>
                                        {renderSubComponent({ row, assetMetadata, assetS3List, refMetadata })}
                                    </td>
                                </tr>
                            )}
                        </React.Fragment>
                    )
                })}
            </tbody>
        </table>
    </>)
}

export function Filter({ column }: { column: Column<any, unknown> }) {
    const columnFilterValue = column.getFilterValue();
    const { filterVariant } = column.columnDef.meta ?? {};
    const sortedUniqueValues = React.useMemo(
        () =>
            filterVariant === 'select'
                ? Array.from(column.getFacetedUniqueValues().keys()).sort()
                : [],
        [column, filterVariant]
    )
    return filterVariant === 'range' ? (
        <div>
            <div className="flex space-x-2">
                {/* See faceted column filters example for min max values functionality */}
                <DebouncedInput
                    type="number"
                    value={(columnFilterValue as [number, number])?.[0] ?? ''}
                    onChange={value =>
                        column.setFilterValue((old: [number, number]) => [value, old?.[1]])
                    }
                    placeholder={`Min`}
                    className="w-24 border shadow rounded"
                />
                <DebouncedInput
                    type="number"
                    value={(columnFilterValue as [number, number])?.[1] ?? ''}
                    onChange={value =>
                        column.setFilterValue((old: [number, number]) => [old?.[0], value])
                    }
                    placeholder={`Max`}
                    className="w-24 border shadow rounded"
                />
            </div>
            <div className="h-1" />
        </div>
    ) : filterVariant === 'select' ? (
        <select
            onChange={e => column.setFilterValue(e.target.value)}
            value={columnFilterValue?.toString()}
        >
            {/* dynamically generated select options from faceted values feature */}
            <option value="">All</option>
            {sortedUniqueValues.map(value => (
                <option value={`${value}`} key={`${value}`}>
                    {`${value}`}
                </option>
            ))}
        </select>
    ) : (
        <DebouncedInput
            className="w-36 border shadow rounded"
            onChange={value => column.setFilterValue(value)}
            placeholder={`Search...`}
            type="text"
            value={(columnFilterValue ?? '') as string}
        />
        // See faceted column filters example for datalist search suggestions
    )
}

// debounce filtering the table
export function DebouncedInput({
    value: initialValue,
    onChange,
    debounce = 500,
    ...props
}: {
    value: string | number
    onChange: (value: string | number) => void
    debounce?: number
} & Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onChange'>) {
    const [value, setValue] = React.useState(initialValue)

    React.useEffect(() => {
        setValue(initialValue)
    }, [initialValue])

    React.useEffect(() => {
        const timeout = setTimeout(() => {
            onChange(value)
        }, debounce)

        return () => clearTimeout(timeout)
    }, [debounce, onChange, value])

    return (
        <input {...props} value={value} onChange={e => setValue(e.target.value)} />
    )
}
