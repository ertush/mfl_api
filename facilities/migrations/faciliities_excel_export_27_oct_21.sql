DROP MATERIALIZED VIEW IF EXISTS facilities_excel_export;

create materialized view facilities_excel_export as
SELECT facilities_facility.id,
       facilities_facility.search,
       facilities_facility.name,
       facilities_facility.official_name                                            AS officialname,
       facilities_facility.code,
       facilities_facility.registration_number,
       facilities_facility.number_of_beds                                           AS beds,
       facilities_facility.number_of_cots                                           AS cots,
       common_ward.name                                                             AS ward_name,
       common_ward.id                                                               AS ward,
       facilities_facility.approved,
       facilities_facility.created,
       facilities_facility.updated,
       facilities_facility.open_whole_day,
       facilities_facility.open_public_holidays,
       facilities_facility.open_weekends,
       facilities_facility.open_late_night,
       facilities_facility.closed,
       facilities_facility.is_published,
       facilities_facility.approved_national_level,
       common_county.name                                                           AS county_name,
       common_county.id                                                             AS county,
       common_constituency.name                                                     AS constituency_name,
       common_constituency.id                                                       AS constituency,
       common_subcounty.name                                                        AS sub_county_name,
       common_subcounty.id                                                          AS sub_county,
       facilities_facilitytype.name                                                 AS facility_type_name,
       facilities_facilitytype.id                                                   AS facility_type,
       facilities_facilitytypecat.name                                              AS facility_type_category,
       facilities_facilitytypecat.id                                                AS facility_type_parent,
       facilities_kephlevel.name                                                    AS keph_level_name,
       facilities_kephlevel.id                                                      AS keph_level,
       facilities_owner.name                                                        AS owner_name,
       facilities_owner.id                                                          AS owner,
       facilities_ownertype.name                                                    AS owner_type_name,
       facilities_ownertype.id                                                      AS owner_type,
       facilities_regulatingbody.name                                               AS regulatory_body_name,
       facilities_regulatingbody.id                                                 AS regulatory_body,
       facilities_facilitystatus.name                                               AS operation_status_name,
       facilities_facilitystatus.id                                                 AS operation_status,
       facilities_facilitystatus.is_public_visible,
       facilities_facilityadmissionstatus.name                                               AS admission_status_name,
       facilities_facilityadmissionstatus.id                                                 AS admission_status,
       st_x(mfl_gis_facilitycoordinates.coordinates)                                AS lat,
       st_y(mfl_gis_facilitycoordinates.coordinates)                                AS long,
       ARRAY(SELECT DISTINCT facilities_facilityservice.service_id
             FROM facilities_facilityservice
             WHERE facilities_facilityservice.facility_id = facilities_facility.id) AS services,
       ARRAY(SELECT DISTINCT facilities_service.category_id
             FROM facilities_facilityservice
                      JOIN facilities_service ON facilities_service.id = facilities_facilityservice.service_id
             WHERE facilities_facilityservice.facility_id = facilities_facility.id) AS categories,
       ARRAY(SELECT DISTINCT facilities_service.name
             FROM facilities_service
                      JOIN facilities_facilityservice ON facilities_service.id = facilities_facilityservice.service_id
             WHERE facilities_facilityservice.facility_id = facilities_facility.id) AS service_names
FROM facilities_facility
         LEFT JOIN facilities_kephlevel ON facilities_kephlevel.id = facilities_facility.keph_level_id
         LEFT JOIN facilities_owner ON facilities_owner.id = facilities_facility.owner_id
         LEFT JOIN facilities_ownertype ON facilities_owner.owner_type_id = facilities_ownertype.id
         LEFT JOIN facilities_facilitytype ON facilities_facilitytype.id = facilities_facility.facility_type_id
         LEFT JOIN facilities_facilitytype facilities_facilitytypecat
                   ON facilities_facilitytypecat.id = facilities_facilitytype.parent_id
         LEFT JOIN facilities_regulatingbody ON facilities_regulatingbody.id = facilities_facility.regulatory_body_id
         LEFT JOIN facilities_facilitystatus ON facilities_facilitystatus.id = facilities_facility.operation_status_id
         LEFT JOIN facilities_facilityadmissionstatus ON facilities_facilityadmissionstatus.id = facilities_facility.admission_status_id
         LEFT JOIN common_ward ON common_ward.id = facilities_facility.ward_id
         LEFT JOIN common_constituency ON common_constituency.id = common_ward.constituency_id
         LEFT JOIN common_subcounty ON common_subcounty.id = common_ward.sub_county_id
         LEFT JOIN common_county ON common_county.id = common_constituency.county_id
         LEFT JOIN mfl_gis_facilitycoordinates ON mfl_gis_facilitycoordinates.facility_id = facilities_facility.id;

alter materialized view facilities_excel_export owner to postgres;

