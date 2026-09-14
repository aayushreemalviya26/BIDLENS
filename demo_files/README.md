# BidLens local acceptance files

Use `tender/GEM_2026_B_7910945.pdf` for the tender flow.

For the combined-file scenario, upload only `bidders/orange_tech_combined/Orange_Tech_Complete_Bid.pdf`. Its GST certificate is on pages 18-19, PAN is on page 20, and Udyam / MSME evidence is on pages 21-22.

For each bidder, create the bidder with the exact identifier and registered name below, then select every PDF in the corresponding folder using the frontend multi-file upload control. The ZIP archives are convenience copies and are not accepted by the PDF uploader.

| Bidder ID | Registered name | PDF folder | Expected initial outcome |
| --- | --- | --- | --- |
| OTS-001 | Orange Tech Systems Private Limited | `bidders/orange_tech/` | COMPLIANT |
| BCS-002 | Bharat Compute Solutions Private Limited | `bidders/bharat_compute/` | NON_COMPLIANT (15% local content) |
| SBS-003 | SecureByte Systems Private Limited | `bidders/securebyte/` | NEEDS_REVIEW (OEM entity ambiguity and no service-centre PDF) |

After the initial Bharat evaluation, upload `mutations/bharat_35/Local_Content_Declaration.pdf` to BCS-002 and process/evaluate again. It has the same filename as the original, so it replaces only that submitted document; local content changes from 15% to 35%.

Every bidder PDF is clearly marked `SYNTHETIC DOCUMENT — FOR PROTOTYPE TESTING ONLY` and uses invented identifiers. No government logos are used.
