# git api v4 note

## references

- https://graphql.github.io/graphql-spec/June2018/#sec-Overview
- https://developer.github.com/v4/
- https://developer.github.com/v4/explorer/
- https://github.com/graphql-python/graphql-core-next/

## search by qualifications

- https://help.github.com/en/github/searching-for-information-on-github/searching-for-repositories
- https://help.github.com/en/github/searching-for-information-on-github/searching-code
- https://help.github.com/en/articles/searching-code
- https://help.github.com/en/articles/finding-files-on-github

```
Exact matches in code search is in beta for a limited number of users and repositories on GitHub, and is subject to change.

You can search code for exact matches that include any combination of letters, numbers, and symbols. For more information, see "Searching code for exact matches."
```

## Considerations for code search

- Due to the complexity of searching code, there are some restrictions on how searches are performed:

- You must be signed in to search for code across all public repositories.

- Code in forks is only searchable if the fork has more stars than the parent repository. Forks with fewer stars than the parent repository are not indexed for code search. To include forks with more stars than their parent in the search results, you will need to add fork:true or fork:only to your query. For more information, see "Searching in forks."

- Only the default branch is indexed for code search. In most cases, this will be the master branch.

- Only files smaller than 384 KB are searchable.

- Only repositories with fewer than 500,000 files are searchable.

- Users who are signed in can search all public repositories.

- Except with filename searches, you must always include at least one search term when searching source code. For example, searching for language:javascript is not valid, while amazing language:javascript is.

- At most, search results can show two fragments from the same file, but there may be more results within the file.

- You can't use the following wildcard characters as part of your search query: `. , : ; / \ `` ' " = * ! ? # $ & + ^ | ~ < > ( ) { } [ ]`. The search will simply ignore these symbols.

## search with fragments

```
query{
  search(first:10,query:"graphql org:github",type:REPOSITORY){
    userCount
    repositoryCount
    issueCount
    codeCount
    wikiCount
    pageInfo{
	  hasNextPage
    }
    edges{
      node{
        __typename
      	...repo
      }
    }
  }
}
fragment repo on Repository{
  name
  id
}
```

## GraphQL Github Example

### Search for top ten stargazers via query

```
// Try at : https://graphql-explorer.githubapp.com/
// With query variables below
// { "queryString": "language:JavaScript stars:>10000" }

query SearchMostTop10Star($queryString: String!) {
  search(query: $queryString, type: REPOSITORY, first: 10) {
    repositoryCount
    edges {
      node {
        ... on Repository {
          name
          descriptionHTML
          stargazers {
            totalCount
          }
          forks {
            totalCount
          }
          updatedAt
        }
      }
    }
  }
}
```


### Search repository
```
{
  search(first: 10, query: "graphql org:github", type: REPOSITORY) {
    userCount
    repositoryCount
    issueCount
    codeCount
    wikiCount
    pageInfo {
      hasNextPage
    }
    edges {
      node {
        __typename
        ... on Repository {
          id
          name
          url
          description
          createdAt
          updatedAt
          pushedAt
          sshUrl
          mentionableUsers(first:0){
            totalCount
          }
          assignableUsers(first:10){
            totalCount
          }
          parent{
            id
            nameWithOwner
            languages(first:1){
              totalCount
            }
          }
          primaryLanguage{
            name
          }
          languages(first:10){
            totalSize
            totalCount
            edges{
              node{
                id
                name
              }
            }
          }
          stargazers {
            totalCount
          }
          forks {
            totalCount
          }
        }
      }
    }
  }
}

```