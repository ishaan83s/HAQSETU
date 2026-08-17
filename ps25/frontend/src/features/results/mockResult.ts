import type { LegalAwarenessResult } from './types'

export const mockResult: LegalAwarenessResult = {
  incidentSummary:
    'You described a situation that may require legal awareness, documentation, and support.',

  possibleIssue:
    'The situation may involve a rights-related concern. A qualified authority or legal-aid provider can help you understand the available options.',

  urgency: 'high',

  urgencyMessage:
    'If you feel unsafe or face an immediate threat, seek emergency assistance first.',

  evidenceChecklist: [
    'Save relevant messages, emails, photographs, and recordings.',
    'Write down important dates, times, locations, and names.',
    'Keep copies of any complaint, notice, receipt, or official document.',
  ],

  nextSteps: [
    {
      title: 'Preserve your records',
      description:
        'Keep original evidence safe and make copies where possible.',
    },
    {
      title: 'Seek legal-aid support',
      description:
        'Contact a suitable legal-services authority or a qualified legal professional for guidance.',
    },
    {
      title: 'Use an official channel',
      description:
        'If appropriate, submit a complaint through the relevant official authority.',
    },
  ],

  officialResources: [
    {
      name: 'National Legal Services Authority (NALSA)',
      description: 'Official information about legal aid and legal services.',
      url: 'https://nalsa.gov.in/legal-services/',
    },
    {
      name: 'Emergency Response Support System (ERSS)',
      description:
        'For immediate emergencies involving safety, police, fire, or medical support.',
      url: 'https://112.gov.in/',
    },
  ],

  disclaimer:
    'HAQSETU provides legal awareness and navigation support. It does not provide legal advice or representation.',
}

export const sampleScenarios: Record<string, { label: string; data: LegalAwarenessResult }> = {
  wage_nonpayment: {
    label: 'Wage Non-Payment',
    data: {
      incidentSummary:
        'You reported working as a skilled technician in Pune for 3 consecutive months without receiving contractually agreed monthly wages totaling ₹45,000.',
      possibleIssue:
        'Under the Payment of Wages Act & Code on Wages, employers cannot withhold earned remuneration without statutory cause. You may be entitled to claim unpaid dues along with compensation.',
      urgency: 'high',
      urgencyMessage:
        'Wage claims have strict statutory limitation periods. Initiating evidence preservation early is critical.',
      evidenceChecklist: [
        'Appointment letter, employment contract, or work order.',
        'Salary slips, bank account statements showing missing deposits, and PF records.',
        'Timesheets, attendance logs, gate registers, or client email sign-offs.',
        'WhatsApp/SMS or email communications demanding payment and manager replies.',
      ],
      nextSteps: [
        {
          title: 'Issue a formal written demand notice',
          description:
            'Draft a dated written communication specifying exact unpaid months, dues calculation, and a reasonable response timeframe.',
        },
        {
          title: 'File a complaint with the Labour Commissioner',
          description:
            'Submit a grievance through the state labour authority or Shram Suvidha portal under the Payment of Wages Act.',
        },
        {
          title: 'Consult Legal Services Authority (DLSA)',
          description:
            'Eligible workers can receive free legal assistance from the District Legal Services Authority to pursue conciliation.',
        },
      ],
      officialResources: [
        {
          name: 'Ministry of Labour & Employment — Shram Suvidha',
          description: 'Official portal for labour grievance filing and compliance inspection.',
          url: 'https://shramsuvidha.gov.in/',
        },
        {
          name: 'National Legal Services Authority (NALSA)',
          description: 'Free legal aid clinics and empanelled advocates for working citizens.',
          url: 'https://nalsa.gov.in/legal-services/',
        },
      ],
      disclaimer:
        'HAQSETU provides legal awareness and navigation support. It does not provide legal advice or representation.',
    },
  },
  tenancy_eviction: {
    label: 'Illegal Tenancy Eviction',
    data: {
      incidentSummary:
        'Your landlord issued a verbal 48-hour eviction notice, threatened power disconnection, and refused to return the ₹60,000 security deposit.',
      possibleIssue:
        'Model Tenancy Act and state rent control provisions protect tenants from arbitrary eviction without due process or valid notice. Cutting off essential utilities constitutes an illegal practice.',
      urgency: 'emergency',
      urgencyMessage:
        'Threats of unlawful eviction or utility disconnection require immediate documentation and police/legal-aid intervention.',
      evidenceChecklist: [
        'Registered or notarized Rent / Lease Agreement.',
        'Rent payment receipts, UPI transaction IDs, or bank transfers.',
        'Security deposit receipt or bank transfer proof.',
        'Recordings, messages, or witnesses regarding verbal threats or utility cutoffs.',
      ],
      nextSteps: [
        {
          title: 'Preserve physical access and utilities',
          description:
            'Do not vacate under coercion. Landlords cannot forcibly evict without an order from the Rent Authority/Court.',
        },
        {
          title: 'File an emergency police report (Non-Cognizable/FIR)',
          description:
            'If facing physical threats, lockouts, or disconnected water/electricity, contact local police station immediately.',
        },
        {
          title: 'Approach Rent Authority or Civil Court for injunction',
          description:
            'Seek an urgent interim injunction restraining the landlord from illegal dispossession.',
        },
      ],
      officialResources: [
        {
          name: 'ERSS Emergency Helpline (112)',
          description: 'Immediate police protection against forced lockout or physical intimidation.',
          url: 'https://112.gov.in/',
        },
        {
          name: 'District Legal Services Authority (DLSA)',
          description: 'Urgent legal representation and dispute mediation for tenant rights.',
          url: 'https://nalsa.gov.in/legal-services/',
        },
      ],
      disclaimer:
        'HAQSETU provides legal awareness and navigation support. It does not provide legal advice or representation.',
    },
  },
  wrongful_termination: {
    label: 'Wrongful Termination',
    data: {
      incidentSummary:
        'You were abruptly terminated without mandatory 30-day notice, inquiry, or severance pay following a legitimate internal workplace grievance.',
      possibleIssue:
        'Retaliatory termination and dismissal without following due inquiry or statutory notice violate Industrial Employment Standing Orders and natural justice principles.',
      urgency: 'medium',
      urgencyMessage:
        'Preserve all employment communications immediately before company portal access is revoked.',
      evidenceChecklist: [
        'Official termination email or letter.',
        'Employment contract detailing notice period and termination clauses.',
        'Past performance appraisals, appreciation emails, and attendance records.',
        'Copies of internal grievance submissions and management correspondence.',
      ],
      nextSteps: [
        {
          title: 'Request formal written grounds for dismissal',
          description:
            'Write to HR requesting itemized severance calculation, relieving letter, and detailed reasons in writing.',
        },
        {
          title: 'Check applicable state Shops & Establishments Act',
          description:
            'Review statutory notice compensation requirements applicable to your establishment category.',
        },
        {
          title: 'Approach Labour Conciliation Officer',
          description:
            'Submit a petition for conciliation or reinstatement through the regional Labour Officer.',
        },
      ],
      officialResources: [
        {
          name: 'SAMADHAN Labour Portal',
          description: 'Online dispute resolution and conciliation filing mechanism.',
          url: 'https://samadhan.labour.gov.in/',
        },
        {
          name: 'State Legal Services Authority (SLSA)',
          description: 'Legal aid counsel for wrongful discharge and employment disputes.',
          url: 'https://nalsa.gov.in/legal-services/',
        },
      ],
      disclaimer:
        'HAQSETU provides legal awareness and navigation support. It does not provide legal advice or representation.',
    },
  },
}