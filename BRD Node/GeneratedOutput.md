# Business Requirement Document (BRD)

## 1. Purpose
The purpose of this project is to modernize the technology stack and leverage AWS cloud to provide faster analytics and insights.

## 2. Project Summary
The project involves recreating the existing data warehouse from an on-premise Oracle database into AWS Redshift. This migration aims to enhance performance, scalability, and accessibility of data analytics.

## 3. Project Success Criteria
- Successful migration of all tables and stored procedures from Oracle to Redshift.
- Seamless integration of data using AWS Glue and EMR.
- Improved query performance and reduced latency in data processing.
- Minimal disruption to existing business operations during migration.
- Stakeholder satisfaction with the new system's performance and capabilities.

## 4. Project Objectives
- Recreate the existing data warehouse in AWS Redshift.
- Ensure data integrity and consistency during the migration process.
- Optimize data integration workflows using AWS Glue and EMR.
- Provide training and documentation for stakeholders to utilize the new system effectively.

## 5. In-Scope
- Table migration from Oracle to Redshift.
- Stored procedure migration from Oracle to Redshift.
- Data integration using AWS Glue and EMR.

## 6. Out of Scope
- Infrastructure setup.
- PII data processing.
- Administrative tasks.

## 7. Non-Functional Requirements
- **Performance**: The new system should provide faster query responses and handle large volumes of data efficiently.
- **Scalability**: The solution should be scalable to accommodate future data growth.
- **Security**: Ensure data security and compliance with relevant regulations.
- **Availability**: The system should have high availability and minimal downtime.
- **Usability**: The system should be user-friendly and provide comprehensive documentation for users.

## 8. Assumptions
- Existing data warehouse schema and data are well-documented.
- AWS services (Redshift, Glue, EMR) are available and configured correctly.
- Stakeholders are available for requirements gathering and testing.
- Adequate network bandwidth is available for data transfer during migration.

## 9. Dependencies
- Availability of AWS Redshift, Glue, and EMR services.
- Access to the existing Oracle database.
- Collaboration with IT department for network and security configurations.
- Support from AWS for any technical issues during migration.

## 10. Constraints
- Limited budget for migration tools and services.
- Time constraints to complete the migration within the planned schedule.
- Dependency on external vendors for certain AWS services.
- Potential downtime during migration affecting business operations.

## 11. Stakeholder Analysis
- **IT Department**: Responsible for technical implementation and support.
- **Marketing Teams**: Utilize analytics for strategic decision-making.
- **Dealers**: Access insights to improve sales and customer engagement.

## 12. Roles and Responsibilities
- **Project Manager**: Oversee the project, manage timelines, and coordinate with stakeholders.
- **Data Engineers**: Execute the migration of tables and stored procedures, ensure data integrity.
- **AWS Specialists**: Configure and optimize AWS services (Redshift, Glue, EMR).
- **Business Analysts**: Gather requirements, validate data, and ensure business needs are met.
- **QA Team**: Test the migrated data and processes to ensure accuracy and performance.

---

This document outlines the requirements and scope for the Oracle to Redshift migration project, ensuring a clear understanding of objectives, responsibilities, and expectations for all stakeholders involved.
