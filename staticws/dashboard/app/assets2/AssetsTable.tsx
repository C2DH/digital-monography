'use client'

import React from 'react';
import {
    Column,
    ColumnDef,
    ColumnFiltersState,
    flexRender,
    getCoreRowModel,
    getExpandedRowModel,
    getFilteredRowModel,
    getSortedRowModel,
    RowData,
    Row,
    SortingFn,
    SortingState,
    useReactTable,
} from '@tanstack/react-table';


type Person = {
    firstName: string,
    lastName: string,
    age: number,
    visits: number,
    progress: number,
    createdAt: Date,
    status: string,
    rank: number,
}

const person1: Person = {
    firstName: "Jeff",
    lastName: "Belzebos",
    age: 99,
    visits: 1,
    progress: 3,
    createdAt: new Date(1999, 1, 1),
    status: "cool-guy",
    rank: 1,
}
const person2: Person = {
    firstName: "Bill",
    lastName: "Gates of Hell",
    age: 666,
    visits: 1,
    progress: 3,
    createdAt: new Date(2004, 2, 25),
    status: "cool-guy",
    rank: 1,
}
const person3: Person = {
    firstName: "Larry",
    lastName: "Hellison",
    age: 999,
    visits: 1,
    progress: 3,
    createdAt: new Date(2020, 1, 15),
    status: "db-guy",
    rank: 1,
}

//custom sorting logic for one of our enum columns
const sortStatusFn: SortingFn<Person> = (rowA, rowB, _columnId) => {
    const statusA = rowA.original.status;
    const statusB = rowB.original.status;
    const statusOrder = ['cool-guy', 'db-guy', 'lame-guy'];
    return statusOrder.indexOf(statusA) - statusOrder.indexOf(statusB);
}

const renderSubComponent = ({ row }: { row: Row<Person> }) => {
    return (
        <pre style={{ fontSize: '10px' }}>
            <code>{JSON.stringify(row.original, null, 2)}</code>
        </pre>
    )
}

export default function AssetsTable(): React.JSX.Element {
    const [sorting, setSorting] = React.useState<SortingState>([]);
    const columns: ColumnDef<Person>[] = [
        {
            id: 'expander',
            header: () => null,
            cell: ({ row }) => {
                console.log("expand action");
                console.log("row.getIsExpanded()", row.getIsExpanded());
                return row.getCanExpand() ? (
                    <button
                        {...{
                            onClick: row.getToggleExpandedHandler(),
                            style: { cursor: 'pointer' },
                        }}
                    >
                        {row.getIsExpanded() ? '👇' : '👉'}
                    </button>
                ) : (
                    '🔵'
                )
            },
        },
        {
            accessorKey: 'firstName',
            cell: info => info.getValue(),
            //this column will sort in ascending order by default since it is a string column
        },
        {
            accessorFn: row => row.lastName,
            id: 'lastName',
            cell: info => info.getValue(),
            header: () => <span>Last Name</span>,
            sortUndefined: 'last', //force undefined values to the end
            sortDescFirst: false, //first sort order will be ascending (nullable values can mess up auto detection of sort order)
        },
        {
            accessorKey: 'age',
            header: () => 'Age',
            //this column will sort in descending order by default since it is a number column
            meta: {
                filterVariant: 'range',
            },
        },
        {
            accessorKey: 'visits',
            header: () => <span>Visits</span>,
            sortUndefined: 'last', //force undefined values to the end
        },
        {
            accessorKey: 'status',
            header: 'Status',
            sortingFn: sortStatusFn, //use our custom sorting function for this enum column
            meta: {
                filterVariant: 'select',
            },
        },
        {
            accessorKey: 'createdAt',
            header: 'Created At',
            // sortingFn: 'datetime' //make sure table knows this is a datetime column (usually can detect if no null values)
        },
    ]
    const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>(
        []
    )
    const [data, setData] = React.useState<Person[]>([person1, person2, person3]);
    const table = useReactTable({
        columns,
        data,
        debugTable: true,
        debugHeaders: true,
        debugColumns: false,
        filterFns: {},
        getCoreRowModel: getCoreRowModel(),
        getExpandedRowModel: getExpandedRowModel(),
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

    console.log(table.getState().sorting);
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
                                        {renderSubComponent({ row })}
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


function Filter({ column }: { column: Column<any, unknown> }) {
    const columnFilterValue = column.getFilterValue();
    const { filterVariant } = column.columnDef.meta ?? {};

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
            {/* See faceted column filters example for dynamic select options */}
            <option value="">All</option>
            <option value="cool-guy">cool-guy</option>
            <option value="db-guy">db-guy</option>
            <option value="lame-guy">lame-guy</option>
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

// A typical debounced input react component
function DebouncedInput({
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
    }, [value])

    return (
        <input {...props} value={value} onChange={e => setValue(e.target.value)} />
    )
}
