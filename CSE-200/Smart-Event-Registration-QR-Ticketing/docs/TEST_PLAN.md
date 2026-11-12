# EventPass — Test Plan

| ID | Scenario | Expected result |
|---|---|---|
| T01 | Open home page | Public landing page loads |
| T02 | Access organizer dashboard without login | Redirects to organizer login |
| T03 | Login with correct credentials | Organizer dashboard opens |
| T04 | Login with wrong password | Login rejected |
| T05 | Create an event | Event saved as Draft |
| T06 | Open a Draft event's registration URL | Registration cannot be submitted |
| T07 | Publish an event | Event appears in public directory |
| T08 | Submit valid participant registration | Registration created as Pending |
| T09 | Submit same email for same event | Duplicate registration blocked |
| T10 | Approve registration | Ticket token generated, PDF bytes stored in the database |
| T11 | SMTP configured | Ticket PDF email delivered |
| T12 | SMTP missing/fails | PDF remains downloadable; local `.eml` preview saved (hosted preview is logged) |
| T13 | Scan correct ticket with gate open | Valid; check-in timestamp saved |
| T14 | Scan same ticket again | Duplicate; second entry rejected |
| T15 | Scan random token | Invalid; attempt logged |
| T16 | Scan a ticket from a different event | Invalid; event mismatch logged |
| T17 | Scan with gate closed | Closed; attempt logged |
| T18 | Reissue an approved ticket | New QR works; previous QR becomes invalid |
| T19 | Export CSV | Participant and check-in fields exported |
| T20 | Scan from a phone over HTTPS | Mobile camera can access the scanner |

## Manual event-day rehearsal

- Use at least two different screens/phones to test QR presentation.
- Test one valid ticket, one duplicate, one random/modified QR and one ticket from a different event.
- Test two gate devices using the same server and database.
- Test camera permission denied, browser refresh, network interruption and scanner reconnection.
- Test a real controlled email inbox before issuing tickets to participants.
- Check that the server computer time and event time zone are correct.
