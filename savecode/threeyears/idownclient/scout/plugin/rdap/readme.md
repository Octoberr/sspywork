
# Terms #
- IANA - Internet Assigned Numbers Authority
- IRR - Internet Routing Registry
- ASN - Globally unique identifier used for routing information exchange with Autonomous Systems.

# RDAP #
The Registration Data Access Protocol (RDAP) was
designed by the Weirds Working Group of the Internet
Engineering Task Force as a successor to the  WHOIS
protocol.
RDAP provides a way to query registration data using
a RESTful web service and uniform query patterns.
The  service is implemented using the Hypertext
Transfer Protocol (HTTP)

# 五大IANA地区 #
## africa 非洲地区 ##
    http://www.afrinic.net/cgi-bin/whois (web ui search)

    https://rdap.afrinic.net/rdap/ip/192.0.20/23 (ip whois)

    https://rdap.afrinic.net/rdap/domain/abc.com

## apnic 亚洲/太平洋地区 ##
    http://wq.apnic.net/apnic-bin/whois.pl (web ui search)

    http://rdap.apnic.net/ip/2001:dc0:2001:11::194 (ip whois)

    http://rdap.apnic.net/history/ip/58.87.97.186 (historical ip whois)

    http://rdap.apnic.net/domain/abc.com (domain whois)


## ARIN 加拿大、美国和一些加勒比海岛屿 ##
    http://whois.arin.net/ui (web ui search)

    https://rdap.arin.net/registry/ip/47.74.44.158 (ip whois)

    https://rdap.arin.net/registry/entity/ABUSE3272-ARIN (entity search)

## LACNIC 拉丁美洲和一些加勒比岛屿 ##
    http://lacnic.net/cgi-bin/lacnic/whois?lg=EN (web ui search)

## ripe 欧洲、中东和中亚 ##

    http://www.ripe.net/perl/whois (web ui search)
    https://stat.ripe.net/docs/data_api
    https://stat.ripe.net/data/whois/data.json?resource=192.0.20/23   (ip whois)
    https://stat.ripe.net/data/reverse-dns/data.json?resource=97.64.37.61 (反向dns解析，ip反查域名)

    https://stat.ripe.net/data/dns-chain/data.json?resource=www.17173.com (rpie-dns解析链，真实IP探测？)


# RFC References #
- RFC7480: HTTP Usage in the Registration Data Access Protocol (RDAP)
- RFC7481: Security Services for the Registration Data Access Protocol (RDAP)
- RFC7482: Registration Data Access Protocol (RDAP) Query Format
- RFC7483: JSON Responses for the Registration Data Access Protocol (RDAP)
- RFC7484: Finding the Authoritative Registration Data (RDAP) Service
- RFC8056: Extensible Provisioning Protocol (EPP) and Registration Data Access Protocol (RDAP) Status Mapping

# RFC 关键内容 #

## RFC 7480 ##

### 5.2.  Redirects ###

   If a server wishes to inform a client that the answer to a given
   query can be found elsewhere, it returns either a 301 (Moved
   Permanently) response code to indicate a permanent move or a 302
   (Found), 303 (See Other), or 307 (Temporary Redirect) response code
   to indicate a non-permanent redirection, and it includes an HTTP(S)
   URL in the Location header field (see [RFC7231]).  The client is
   expected to issue a subsequent request to satisfy the original query
   using the given URL without any processing of the URL.  In other
   words, the server is to hand back a complete URL, and the client
   should not have to transform the URL to follow it.  Servers are under
   no obligation to return a URL conformant to [RFC7482].

   For this application, such an example of a permanent move might be a
   Top-Level Domain (TLD) operator informing a client the information being sought can be found with another TLD operator (i.e., a query
   for the domain bar in foo.example is found at
   http://foo.example/domain/bar).

   For example, if the client uses

      http://serv1.example.com/weirds/domain/example.com

   the server redirecting to

      https://serv2.example.net/weirds2/

   would set the Location: field to the value

      https://serv2.example.net/weirds2/domain/example.com

### Appendix A.  Protocol Example ###
   To demonstrate typical behavior of an RDAP client and server, the
   following is an example of an exchange, including a redirect.  The
   data in the response has been elided for brevity, as the data format
   is not described in this document.  The media type used here is
   described in [RFC7483].

   An example of an RDAP client and server exchange:

     Client:
         <TCP connect to rdap.example.com port 80>
         GET /rdap/ip/203.0.113.0/24 HTTP/1.1
         Host: rdap.example.com
         Accept: application/rdap+json

     rdap.example.com:
         HTTP/1.1 301 Moved Permanently
         Location: http://rdap-ip.example.com/rdap/ip/203.0.113.0/24
         Content-Length: 0
         Content-Type: application/rdap+json
         <TCP disconnect>

     Client:
         <TCP connect to rdap-ip.example.com port 80>
         GET /rdap/ip/203.0.113.0/24 HTTP/1.1
         Host:  rdap-ip.example.com
         Accept: application/rdap+json

     rdap-ip.example.com:
         HTTP/1.1 200 OK
         Content-Type: application/rdap+json
         Content-Length: 9001

         { ... }
         <TCP disconnect>

## RFC 7482 ##
### 3.1.  Lookup Path Segment Specification ###
A simple lookup to determine if an object exists (or not) without
returning RDAP-encoded results can be performed using the HTTP HEAD
method as described in Section 4.1 of [RFC7480].
The resource type path segments for exact match lookup are:
-  'ip': Used to identify IP networks and associated data referenced
   using either an IPv4 or IPv6 address.
-  'autnum': Used to identify Autonomous System number registrations
   and associated data referenced using an asplain Autonomous System
   number.
-  'domain': Used to identify reverse DNS (RIR) or domain name (DNR)
   information and associated data referenced using a fully qualified
   domain name.
-  'nameserver': Used to identify a nameserver information query
   using a host name.
-  'entity': Used to identify an entity information query using a
   string identifier.

### 3.1.1.  IP Network Path Segment Specification ###

   `Syntax: ip/<IP address> or ip/<CIDR prefix>/<CIDR length>`

   Queries for information about IP networks are of the form `/ip/XXX/...`
   or `/ip/XXX/YY/...`  where the path segment following 'ip' is either an
   IPv4 dotted decimal or IPv6 [RFC5952] address (i.e., XXX) or an IPv4
   or IPv6 Classless Inter-domain Routing (CIDR) [RFC4632] notation
   address block (i.e., XXX/YY).  Semantically, the simpler form using
   the address can be thought of as a CIDR block with a bitmask length
   of 32 for IPv4 and a bitmask length of 128 for IPv6.  A given
   specific address or CIDR may fall within multiple IP networks in a
   hierarchy of networks; therefore, this query targets the "most-
   specific" or smallest IP network that completely encompasses it in a
   hierarchy of IP networks.

   The IPv4 and IPv6 address formats supported in this query are
   described in Section 3.2.2 of RFC 3986 [RFC3986] as IPv4address and
   IPv6address ABNF definitions.  Any valid IPv6 text address format
   [RFC4291] can be used.  This includes IPv6 addresses written using
   with or without compressed zeros and IPv6 addresses containing
   embedded IPv4 addresses.  The rules to write a text representation of
   an IPv6 address [RFC5952] are RECOMMENDED.  However, the zone_id
   [RFC4007] is not appropriate in this context; therefore, the
   corresponding syntax extension in RFC 6874 [RFC6874] MUST NOT be
   used, and servers are to ignore it if possible.

   For example, the following URL would be used to find information for
   the most specific network containing 192.0.2.0:

    https://example.com/rdap/ip/192.0.2.0

   The following URL would be used to find information for the most
   specific network containing 192.0.2.0/24:

    https://example.com/rdap/ip/192.0.2.0/24

   The following URL would be used to find information for the most
   specific network containing 2001:db8::0:

    https://example.com/rdap/ip/2001:db8::0

## RFC 7483 ##
### 10.2.  JSON Values Registry ###

   IANA has created a category in the protocol registries labeled
   "Registration Data Access Protocol (RDAP)", and within that category,
   IANA has established a URL-referenceable, stand-alone registry
   labeled "RDAP JSON Values".  This new registry is for use in the
   notices and remarks (Section 4.3), status (Section 4.6), role
   (Section 5.1), event action (Section 4.5), and domain variant
   relation (Section 5.3) fields specified in RDAP.

   Each entry in the registry contains the following fields:

   1.  Value -- the string value being registered.

   2.  Type -- the type of value being registered.  It should be one of
       the following:

       *  "notice or remark type" -- denotes a type of notice or remark.

       *  "status" -- denotes a value for the "status" object member as
          defined by Section 4.6.

       *  "role" -- denotes a value for the "role" array as defined in
          Section 5.1.

       *  "event action" -- denotes a value for an event action as
          defined in Section 4.5.

       *  "domain variant relation" -- denotes a relationship between a
          domain and a domain variant as defined in Section 5.3.

   3.  Description -- a one- or two-sentence description regarding the
       meaning of the value, how it might be used, and/or how it should
       be interpreted by clients.

   4.  Registrant Name -- the name of the person registering the value.

   5.  Registrant Contact Information -- an email address, postal
       address, or some other information to be used to contact the
       registrant.

   This registry is operated under the "Expert Review" policy defined in
   [RFC5226].

   Review of registrations into this registry by the designated
   expert(s) should be narrowly judged on the following criteria:

   1.  Values in need of being placed into multiple types must be
       assigned a separate registration for each type.

   2.  Values must be strings.  They should be multiple words separated
       by single space characters.  Every character should be
       lowercased.  If possible, every word should be given in English
       and each character should be US-ASCII.

   3.  Registrations should not duplicate the meaning of any existing
       registration.  That is, if a request for a registration is
       significantly similar in nature to an existing registration, the
       request should be denied.  For example, the terms "maintainer"
       and "registrant" are significantly similar in nature as they both
       denote a holder of a domain name or Internet number resource.  In
       cases where it may be reasonably argued that machine
       interpretation of two similar values may alter the operation of
       client software, designated experts should not judge the values
       to be of significant similarity.

   4.  Registrations should be relevant to the common usages of RDAP.
       Designated experts may rely upon the serving of the value by a
       DNR or RIR to make this determination.

   The following sections provide initial registrations into this registry.

### 10.2.1.  Notice and Remark Types ###

   The following values have been registered in the "RDAP JSON Values"
   registry:

      Value: result set truncated due to authorization
      Type: notice and remark type
      Description: The list of results does not contain all results due
         to lack of authorization.  This may indicate to some clients
         that proper authorization will yield a longer result set.
      Registrant Name: IESG
      Registrant Contact Information: iesg@ietf.org
      
      
      Value: result set truncated due to excessive load
      Type: notice and remark type
      Description: The list of results does not contain all results due
         to an excessively heavy load on the server.  This may indicate
         to some clients that requerying at a later time will yield a
         longer result set.
      Registrant Name: IESG
      Registrant Contact Information: iesg@ietf.org


      Value: result set truncated due to unexplainable reasons
      Type: notice and remark type
      Description: The list of results does not contain all results for
         an unexplainable reason.  This may indicate to some clients
         that requerying for any reason will not yield a longer result
         set.
      Registrant Name: IESG
      Registrant Contact Information: iesg@ietf.org


      Value: object truncated due to authorization
      Type: notice and remark type
      Description: The object does not contain all data due to lack of
         authorization.
      Registrant Name: IESG
      Registrant Contact Information: iesg@ietf.org


      Value: object truncated due to excessive load
      Type: notice and remark type
      Description: The object does not contain all data due to an
         excessively heavy load on the server.  This may indicate to
         some clients that requerying at a later time will yield all
         data of the object.
      Registrant Name: IESG
      Registrant Contact Information: iesg@ietf.org


      Value: object truncated due to unexplainable reasons
      Type: notice and remark type
      Description: The object does not contain all data for an
         unexplainable reason.
      Registrant Name: IESG
      Registrant Contact Information: iesg@ietf.org


# BGP（边界网关协议）#
主要用于互联网AS（自治系统）之间的互联，BGP的最主要功能在于控制路由的传播和选择最好的路由。中国网通 、中国电信、中国铁通和一些大的民营IDC运营商都具有AS号，全国各大网络运营商多数都是通过BGP协议与自身的AS号来实现多线互联的。使用此方案来实现多线路互联，IDC需要在CNNIC（中国互联网信息中心）或APNIC（亚太网络信息中心）申请自己的IP地址段和AS号（目前网宿科技同时是APNIC和CNNIC的会员单位），然后通过BGP协议将此段IP地址广播到其它的网络运营商的网络中。使用BGP协议互联后，网络运营商的所有骨干路由设备将会判断到IDC机房IP段的最佳路由，以保证不同网络运营商用户的高速访问。
BGP 机房的优点：
1． 服务器只需要设置一个IP地址，最佳访问路由是由网络上的骨干路由器根据路由跳数与其它技术指标来确定的，不会占用服务器的任何系统资源。服务器的上行路由与下行路由都能选择最优的路径，所以能真正实现高速的单IP高速访问。
2． 由于BGP协议本身具有冗余备份、消除环路的特点，所以当IDC服务商有多条BGP互联线路时可以实现路由的相互备份，在一条线路出现故障时路由会自动切换到其它线路。
3． 使用BGP协议还可以使网络具有很强的扩展性可以将IDC网络与其他运营商互联，轻松实现单IP多线路，做到所有互联运营商的用户访问都很快。这个是双IP双线无法比拟的。