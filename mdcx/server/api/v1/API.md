# File Browser API

This document specifies the RESTful API required by the `FileBrowser` component to list and navigate files and directories on the server.

## Endpoint

`GET /api/files`

This endpoint retrieves the list of items (files and directories) within a specified directory.

### Query Parameters

| Parameter | Type   | Required | Default | Description                                   |
| :-------- | :----- | :------- | :------ | :-------------------------------------------- |
| `path`    | string | No       | `/`     | The absolute path of the directory to browse. |

### Success Response (200 OK)

The response body will be a JSON object containing a `data` key, which holds an array of file/directory items.

#### Response Body Structure

```json
{
  "data": [
    {
      "name": "string",
      "path": "string",
      "type": "string ('file' or 'directory')",
      "size": "number (in bytes, optional)",
      "lastModified": "string (ISO 8601 format, optional)"
    }
  ]
}
```

#### Item Properties

| Property       | Type   | Description                                                  |
| :------------- | :----- | :----------------------------------------------------------- |
| `name`         | string | The name of the file or directory.                           |
| `path`         | string | The full absolute path of the item.                          |
| `type`         | string | The type of the item. Must be either `file` or `directory`.  |
| `size`         | number | The size of the file in bytes. Omitted for directories.      |
| `lastModified` | string | The last modification date and time in ISO 8601 format.      |

#### Example Response

Request: `GET /api/files?path=/home/user/documents`

```json
{
  "data": [
    {
      "name": "Project Alpha",
      "path": "/home/user/documents/Project Alpha",
      "type": "directory",
      "lastModified": "2024-07-27T10:30:00Z"
    },
    {
      "name": "report.pdf",
      "path": "/home/user/documents/report.pdf",
      "type": "file",
      "size": 1048576,
      "lastModified": "2024-07-26T15:00:00Z"
    },
    {
      "name": "notes.txt",
      "path": "/home/user/documents/notes.txt",
      "type": "file",
      "size": 2048,
      "lastModified": "2024-07-28T09:15:00Z"
    }
  ]
}
```

### Error Responses

#### 400 Bad Request

Returned if the `path` parameter is invalid or malformed.

```json
{
  "error": "Invalid path provided."
}
```

#### 404 Not Found

Returned if the specified `path` does not exist.

```json
{
  "error": "Path not found: /path/to/nonexistent/directory"
}
```

#### 500 Internal Server Error

Returned for any other server-side errors.

```json
{
  "error": "An unexpected error occurred on the server."
}
