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
      name: 'National Legal Services Authority',
      description: 'Official information about legal aid and legal services.',
      url: 'https://nalsa.gov.in/legal-services/',
    },
    {
      name: 'Emergency Response Support System',
      description:
        'For immediate emergencies involving safety, police, fire, or medical support.',
      url: 'https://112.gov.in/',
    },
  ],

  disclaimer:
    'HAQSETU provides legal awareness and navigation support. It does not provide legal advice or representation.',
}