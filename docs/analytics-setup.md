# Analytics Setup Guide

## Google Analytics 4 Setup

### Step 1: Create GA4 Property
1. Go to [Google Analytics](https://analytics.google.com/)
2. Create a new GA4 property for `franksunye.github.io`
3. Get your Measurement ID (format: G-XXXXXXXXXX)

### Step 2: Update mkdocs.yml
Replace `G-PLACEHOLDER` in mkdocs.yml with your actual Measurement ID:

```yaml
extra:
  analytics:
    provider: google
    property: G-YOUR-ACTUAL-ID  # Replace this
```

### Step 3: Google Search Console
1. Go to [Google Search Console](https://search.google.com/search-console/)
2. Add property: `https://franksunye.github.io/quantdb/`
3. Verify ownership using GA4 (automatic if same Google account)
4. Submit sitemap: `https://franksunye.github.io/quantdb/sitemap.xml`

## UTM Parameter Strategy

### Campaign Tracking URLs

#### Reddit Campaign
- PyPI: `https://pypi.org/project/quantdb/?utm_source=reddit&utm_medium=social&utm_campaign=launch`
- GitHub: `https://github.com/franksunye/quantdb?utm_source=reddit&utm_medium=social&utm_campaign=launch`
- Docs: `https://franksunye.github.io/quantdb/?utm_source=reddit&utm_medium=social&utm_campaign=launch`

#### 知乎 Campaign
- PyPI: `https://pypi.org/project/quantdb/?utm_source=zhihu&utm_medium=article&utm_campaign=launch`
- GitHub: `https://github.com/franksunye/quantdb?utm_source=zhihu&utm_medium=article&utm_campaign=launch`
- Docs: `https://franksunye.github.io/quantdb/?utm_source=zhihu&utm_medium=article&utm_campaign=launch`

#### CSDN Campaign
- PyPI: `https://pypi.org/project/quantdb/?utm_source=csdn&utm_medium=blog&utm_campaign=launch`
- GitHub: `https://github.com/franksunye/quantdb?utm_source=csdn&utm_medium=blog&utm_campaign=launch`
- Docs: `https://franksunye.github.io/quantdb/?utm_source=csdn&utm_medium=blog&utm_campaign=launch`
## Key Metrics to Track

### Primary KPIs
- **Documentation site visits**: Monthly unique visitors
- **PyPI downloads**: Weekly/monthly download count
- **GitHub metrics**: Stars, forks, issues, PRs
- **Search rankings**: Position for target keywords

<<<<<<< HEAD
### Secondary KPIs
- **Bounce rate**: Documentation engagement
- **Session duration**: User engagement depth
- **Conversion rate**: Docs → PyPI downloads
- **Geographic distribution**: User locations

=======
>>>>>>> 732b31e (🚀 Comprehensive SEO Optimization for GTM Launch)
### Target Goals (3 months)
- Documentation: 1,000+ monthly visitors
- PyPI downloads: 500+ monthly downloads
- GitHub stars: 100+ stars
- Search ranking: Top 3 pages for "python stock data cache"
<<<<<<< HEAD

## Weekly Reporting Template

```markdown
# Week of [DATE] - QuantDB Analytics Report

## Traffic Overview
- Documentation visits: XXX (±XX% vs last week)
- PyPI downloads: XXX (±XX% vs last week)
- GitHub stars: XXX (+XX new this week)

## Top Traffic Sources
1. Source 1: XX% of traffic
2. Source 2: XX% of traffic
3. Source 3: XX% of traffic

## Search Performance
- Average position: X.X
- Click-through rate: X.X%
- Impressions: XXX

## Action Items for Next Week
- [ ] Item 1
- [ ] Item 2
- [ ] Item 3
```
=======
>>>>>>> 732b31e (🚀 Comprehensive SEO Optimization for GTM Launch)
