// Shared Data Shape as per team specification
export const INITIAL_TENDERS = [
  {
    tender_id: "GEM/2024/001",
    title: "Supply of Safety Equipment for Government Schools",
    department: "Ministry of Education",
    bids_count: 8,
    status: "Under Evaluation",
    last_updated: "2026-09-12 11:45 AM",
    published_date: "2026-08-28",
    deadline: "2026-09-25",
    estimated_value: "₹ 4.80 Crore",
    checklist_approved: false,
    requirements: [
      {
        requirement_id: "REQ01",
        name: "GST Registration",
        category: "FINANCIAL",
        operator: "==",
        required_value: 1,
        unit: "Active Certificate",
        source: { clause: "3.1", page: 4 },
        approved: true
      },
      {
        requirement_id: "REQ02",
        name: "Udyam MSME Registration",
        category: "LEGAL",
        operator: "==",
        required_value: 1,
        unit: "Valid Document",
        source: { clause: "4.2", page: 7 },
        approved: true
      },
      {
        requirement_id: "REQ03",
        name: "BIS Quality Certification",
        category: "QUALITY",
        operator: "==",
        required_value: 1,
        unit: "IS 9438:2018",
        source: { clause: "5.4", page: 10 },
        approved: true
      },
      {
        requirement_id: "REQ04",
        name: "OEM Authorization Letter",
        category: "AUTHORIZATION",
        operator: "==",
        required_value: 1,
        unit: "Direct MAF",
        source: { clause: "6.1", page: 12 },
        approved: true
      },
      {
        requirement_id: "REQ05",
        name: "Local Content",
        category: "POLICY",
        operator: ">=",
        required_value: 50,
        unit: "%",
        source: { clause: "8.2", page: 14 },
        approved: true
      },
      {
        requirement_id: "REQ06",
        name: "Average Annual Turnover",
        category: "FINANCIAL",
        operator: ">=",
        required_value: 5,
        unit: "Cr",
        source: { clause: "9.3", page: 18 },
        approved: true
      },
      {
        requirement_id: "REQ07",
        name: "Past Execution Experience",
        category: "EXPERIENCE",
        operator: ">=",
        required_value: 3,
        unit: "Years",
        source: { clause: "10.1", page: 22 },
        approved: true
      }
    ]
  },
  {
    tender_id: "GEM/2024/002",
    title: "Procurement of High-Performance Server Infrastructure",
    department: "Ministry of Electronics & IT",
    bids_count: 14,
    status: "Checklist Approved",
    last_updated: "2026-09-11 04:20 PM",
    published_date: "2026-08-15",
    deadline: "2026-09-18",
    estimated_value: "₹ 12.50 Crore",
    checklist_approved: true,
    requirements: [
      {
        requirement_id: "REQ201",
        name: "ISO 27001 Security Standard",
        category: "QUALITY",
        operator: "==",
        required_value: 1,
        unit: "Valid Cert",
        source: { clause: "2.1", page: 5 },
        approved: true
      },
      {
        requirement_id: "REQ202",
        name: "Class-1 Local Supplier",
        category: "POLICY",
        operator: ">=",
        required_value: 60,
        unit: "%",
        source: { clause: "4.5", page: 11 },
        approved: true
      },
      {
        requirement_id: "REQ203",
        name: "Annual IT Turnover",
        category: "FINANCIAL",
        operator: ">=",
        required_value: 15,
        unit: "Cr",
        source: { clause: "7.2", page: 19 },
        approved: true
      }
    ]
  },
  {
    tender_id: "GEM/2024/003",
    title: "Construction of Solar Microgrid Stations in Remote Dist",
    department: "Ministry of New & Renewable Energy",
    bids_count: 5,
    status: "Under Evaluation",
    last_updated: "2026-09-10 09:15 AM",
    published_date: "2026-09-01",
    deadline: "2026-10-05",
    estimated_value: "₹ 8.20 Crore",
    checklist_approved: false,
    requirements: [
      {
        requirement_id: "REQ301",
        name: "MNRE Empanelment",
        category: "LEGAL",
        operator: "==",
        required_value: 1,
        unit: "Active License",
        source: { clause: "1.4", page: 3 },
        approved: true
      },
      {
        requirement_id: "REQ302",
        name: "Solar Cell Domestic Content",
        category: "POLICY",
        operator: ">=",
        required_value: 75,
        unit: "%",
        source: { clause: "5.1", page: 16 },
        approved: true
      }
    ]
  },
  {
    tender_id: "GEM/2024/004",
    title: "Supply of Medical Diagnostic Kits for Primary Health Centers",
    department: "Ministry of Health & Family Welfare",
    bids_count: 0,
    status: "Draft",
    last_updated: "2026-09-09 02:10 PM",
    published_date: "2026-09-08",
    deadline: "2026-10-12",
    estimated_value: "₹ 3.10 Crore",
    checklist_approved: false,
    requirements: [
      {
        requirement_id: "REQ401",
        name: "CDSCO Manufacturing License",
        category: "LEGAL",
        operator: "==",
        required_value: 1,
        unit: "Form MD-9",
        source: { clause: "3.3", page: 6 },
        approved: true
      }
    ]
  }
];

export const MOCK_TENDER_DOCUMENT = {
  tender_id: "GEM/2024/001",
  title: "Supply of Safety Equipment for Government Schools",
  clauses: [
    {
      clause: "3.1",
      page: 4,
      title: "Taxation & GST Compliance",
      text: "The bidder must possess a valid Goods and Services Tax (GST) Registration Certificate issued by the competent authority in India. Active status must be verified on the GST portal at time of submission."
    },
    {
      clause: "4.2",
      page: 7,
      title: "MSME & Udyam Portal Verification",
      text: "Bidders claiming purchase preference or exemption under Micro and Small Enterprises (MSEs) policy must submit a valid Udyam Registration Certificate. Micro & Small Enterprises are exempted from EMD deposit."
    },
    {
      clause: "5.4",
      page: 10,
      title: "Bureau of Indian Standards (BIS) Marking",
      text: "All safety equipment supplied under this contract must strictly adhere to BIS standard IS 9438:2018. Test reports from NABL-accredited laboratories dated within the last 12 months must be enclosed with Volume 1."
    },
    {
      clause: "6.1",
      page: 12,
      title: "Original Equipment Manufacturer (OEM) Authorization",
      text: "If the bidder is not the OEM, a Manufacturer's Authorization Form (MAF) explicitly granting authorization to quote for Tender GEM/2024/001 must be attached. Generic dealer agreements will be rejected."
    },
    {
      clause: "8.2",
      page: 14,
      title: "Make in India & Local Content Mandate",
      text: "Under Public Procurement (Preference to Make in India) Order, prime contractors must certify a minimum of 50% Local Content. Subcontracting foreign parts beyond 50% shall lead to immediate disqualification."
    },
    {
      clause: "9.3",
      page: 18,
      title: "Financial Eligibility & Annual Turnover",
      text: "The average annual financial turnover of the bidder during the last three financial years (FY 2022-23, 2023-24, 2024-25) must be at least ₹5 Crore, as verified by a Chartered Accountant certificate with valid UDIN."
    },
    {
      clause: "10.1",
      page: 22,
      title: "Past Execution & Technical Capability",
      text: "The bidder must have completed at least 3 years of continuous operation in supplying industrial or educational safety equipment to Central/State Govt departments or PSUs with satisfactory completion certificates."
    }
  ]
};
