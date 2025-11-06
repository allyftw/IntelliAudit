# Control 5.1 Evidence Schema Expansion Plan

## Control Text (ISO 27001:2022)
"Information security policy and topic-specific policies shall be defined, approved by management, published, communicated to and acknowledged by relevant personnel and relevant interested parties and reviewed at planned intervals and if significant changes occur."

## Current Evidence Schema

**File**: `Output/ISO27001_Policy_Evidence.csv`

**Current Fields**:
- Document ID
- Document Name
- Version
- Approval Date
- Approved By
- Review Date
- Next Review
- Distribution List
- Acknowledgment Count
- Control Reference

## Required Evidence Fields (Full Control Coverage)

### ✅ Currently Covered
1. **Defined** - ✅ Document ID, Document Name, Version
2. **Approved by management** - ✅ Approval Date, Approved By
3. **Reviewed at planned intervals** - ✅ Review Date, Next Review
4. **Acknowledged** - ✅ Acknowledgment Count (partial - count only)

### ⚠️ Partially Covered
5. **Published** - ⚠️ Inferred from Distribution List (not explicit)
6. **Communicated** - ⚠️ Inferred from Distribution List (not explicit)
7. **Relevant personnel and interested parties** - ⚠️ Distribution List exists but not structured

### ❌ Missing Fields
8. **Reviewed if significant changes occur** - ❌ Not tracked
9. **Topic-specific policies** - ❌ Not linked to main policy
10. **Acknowledgment details** - ❌ Only count, not who/when

## Recommended Schema Expansion

### Priority 1: Critical Additions

```csv
# Add to ISO27001_Policy_Evidence.csv

# Publication & Communication
Published Date,YYYY-MM-DD,Date policy was published/made available
Publication Status,Published/Draft/Archived,Explicit publication status
Communication Date,YYYY-MM-DD,Date policy was communicated to stakeholders
Communication Method,Email/Portal/Meeting/Other,How policy was communicated

# Acknowledgment Details
Acknowledgment Rate (%),0-100,Percentage of recipients who acknowledged
Employee Count,Integer,Total number of employees
Contractor Count,Integer,Total number of contractors
Third Party Count,Integer,Total number of third parties
Acknowledgment Deadline,YYYY-MM-DD,Deadline for acknowledgments

# Change Management
Significant Change Date,YYYY-MM-DD,Date of significant change (if applicable)
Change Description,Text,Description of significant change
Change-Triggered Review,Yes/No,Whether review was triggered by change
Change-Triggered Review Date,YYYY-MM-DD,Date of change-triggered review

# Topic-Specific Policy Linkage
Main Policy ID,Text,ID of main Information Security Policy (for topic-specific policies)
Linked Topic Policies,Text,Comma-separated list of topic-specific policy IDs
Policy Framework Complete,Yes/No,Whether full policy framework exists
```

### Priority 2: Enhanced Tracking

```csv
# Additional fields for comprehensive coverage

# Review Schedule
Review Interval (months),Integer,Planned review interval in months
Last Review Type,Scheduled/Change-Triggered/Ad-Hoc,Type of last review
Review Frequency,Annual/Bi-Annual/Quarterly,Planned review frequency

# Coverage Metrics
Personnel Coverage (%),0-100,Percentage of personnel covered
Interested Party Coverage (%),0-100,Percentage of interested parties covered
Distribution Method,Email/Portal/In-Person/Other,Primary distribution method

# Compliance Indicators
Policy Accessible,Yes/No,Whether policy is accessible to all stakeholders
Policy Version Control,Yes/No,Whether version control is maintained
Policy Archive Status,Active/Archived/Deprecated,Current status
```

## Seed Data Generation Requirements

### For Realistic Test Data:

1. **Main Information Security Policy**
   - Published Date: Recent (within 6 months)
   - Acknowledgment Count: 800-1000 (high)
   - Employee Count: 1000
   - Contractor Count: 150
   - Third Party Count: 50
   - Acknowledgment Rate: 85-95%

2. **Topic-Specific Policies** (linked to main)
   - Access Control Policy (5.15)
   - Data Classification Policy (5.12)
   - Incident Response Policy (5.24)
   - Asset Management Policy (5.9)
   - Business Continuity Policy (5.29)

3. **Review Schedule**
   - Last Review: Within last 6 months
   - Next Review: Within next 6 months
   - Review Interval: 12 months
   - Change-Triggered Reviews: 0-2 in last year

## Implementation Priority

### Phase 1: Minimum Viable (POC)
Add these 3 fields to existing schema:
- `Published Date`
- `Acknowledgment Rate (%)`
- `Significant Change Date`

### Phase 2: Enhanced Coverage
Add communication and coverage tracking:
- `Communication Date`
- `Employee Count`
- `Contractor Count`
- `Change-Triggered Review`

### Phase 3: Full Framework
Add topic-specific policy linkage and comprehensive tracking

## Test Coverage Requirements

The test suite (`test_control_5_1_policy.py`) should validate:

1. ✅ All 8 control requirements
2. ✅ Edge cases (missing fields, invalid dates)
3. ✅ Multiple evidence records
4. ✅ Topic-specific policy linkage (when implemented)
5. ✅ Change-triggered reviews (when implemented)

## Next Steps

1. **Update Evidence Schema**: Add Priority 1 fields to CSV
2. **Generate Seed Data**: Create realistic test data with new fields
3. **Enhance Evaluator**: Update `_evaluate_policy_control()` to use new fields
4. **Update Tests**: Tests already written to document gaps and test new fields when added

