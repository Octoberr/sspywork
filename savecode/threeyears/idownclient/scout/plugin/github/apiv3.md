## search code


gitapiv3用于直接使用关键字搜索代码

这样搜是可以的：
```
https://api.github.com/search/code?q=add
```

加关键字或用curl也是可以的：
```
https://api.github.com/search/code?q=addClass+in:file+language:python


curl -H "Authorization: token OAUTH-TOKEN" https://api.github.com
```


## OAuth2.0

OAuth2.0认证时，需要以HTTP头的方式发送认证授权码，才能请求到想要的资源

```
Authorization: Basic czZCaGRSa3F0MzpnWDFmQmF0M2JW
Authorization: Mac czZCaGRSa3F0MzpnWDFmQmF0M2JW
Authorization: Bearer czZCaGRSa3F0MzpnWDFmQmF0M2JW
```