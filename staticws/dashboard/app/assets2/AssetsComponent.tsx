'use client'

import React from 'react';
import {
    ColumnDef,
    ColumnFiltersState,
    SortingFn,
    SortingState,
} from '@tanstack/react-table';
import { renderSubComponent, Table } from './AssetsTable';
import { Person } from "./types";

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
        enableColumnFilter: false,
        // enableSorting: false
        sortingFn: 'datetime' //make sure table knows this is a datetime column
    },
]

export default function AssetsTable(): React.JSX.Element {
    const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([]);
    const [sorting, setSorting] = React.useState<SortingState>([]);
    const [data, setData] = React.useState<Person[]>([person1, person2, person3]);
    return (
        <Table
            data={data}
            columns={columns}
            // getRowCanExpand={() => true}
            renderSubComponent={renderSubComponent}
            columnFilters={columnFilters}
            setColumnFilters={setColumnFilters}
            sorting={sorting}
            setSorting={setSorting}
        ></Table>
    )
}
