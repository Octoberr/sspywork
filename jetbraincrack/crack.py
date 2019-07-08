"""
手动激活的jsoncode
by swm 2019/07/08
"""
import json

a = '''
{
    "licenseId": "ThisCrackLicenseId",
    "licenseeName": "swm",
    "assigneeName": "swm",
    "assigneeEmail": "sepjudy@gmail.com",
    "licenseRestriction": "Thanks Rover12421 Crack",
    "checkConcurrentUse": false,
    "products": [
        {
            "code": "II",
            "paidUpTo": "2022-07-08"
        },
        {
            "code": "DM",
            "paidUpTo": "2022-07-08"
        },
        {
            "code": "AC",
            "paidUpTo": "2022-07-08"
        },
        {
            "code": "RS0",
            "paidUpTo": "2022-07-08"
        },
        {
            "code": "WS",
            "paidUpTo": "2022-07-08"
        },
        {
            "code": "DPN",
            "paidUpTo": "2022-07-08"
        },
        {
            "code": "RC",
            "paidUpTo": "2022-07-08"
        },
        {
            "code": "PS",
            "paidUpTo": "2022-07-08"
        },
        {
            "code": "DC",
            "paidUpTo": "2022-07-08"
        },
        {
            "code": "RM",
            "paidUpTo": "2022-07-08"
        },
        {
            "code": "CL",
            "paidUpTo": "2022-07-08"
        },
        {
            "code": "PC",
            "paidUpTo": "2022-07-08"
        },
        {
            "code": "DB",
            "paidUpTo": "2022-07-08"
        },
        {
            "code": "GO",
            "paidUpTo": "2022-07-08"
        },
        {
            "code": "RD",
            "paidUpTo": "2022-07-08"
        }
    ],
    "hash": "2911276/0",
    "gracePeriodDays": 7,
    "autoProlongated": false
}
'''

print(json.loads(a))
