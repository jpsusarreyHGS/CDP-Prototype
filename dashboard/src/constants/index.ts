export const API_BASE_URL = 'http://127.0.0.1:8000';

export const GA4_METRICS = [
  'totalUsers',
  'sessions',
  'eventCount',
  'screenPageViews',
  'newUsers',
  'conversions',
  'totalRevenue',
  'averageSessionDuration',
  'engagementRate',
  'bounceRate'
] as const;

export const METRIC_DISPLAY_NAMES: Record<string, string> = {
  'totalUsers': 'Total Users',
  'sessions': 'Sessions - Total number of sessions',
  'eventCount': 'Event Count - Total number of events',
  'screenPageViews': 'Screen Page Views - Total page/screen views',
  'newUsers': 'New Users - Number of first-time users',
  'conversions': 'Conversions - Total conversions',
  'totalRevenue': 'Total Revenue - Total revenue (e-commerce)',
  'averageSessionDuration': 'Average Session Duration - Average session duration (seconds)',
  'engagementRate': 'Engagement Rate - Percentage of engaged sessions',
  'bounceRate': 'Bounce Rate - Percentage of bounced sessions'
};

