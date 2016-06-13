-- Table: ddod_smw_links

-- DROP TABLE ddod_smw_links;

/*
Define table for manipulating ...
*/
DROP   TABLE IF EXISTS ddod_smw_links;
CREATE TABLE           ddod_smw_links
(
   id          SERIAL
  ,run_id      BIGINT
  ,categories  VARCHAR
  ,page_id     INTEGER
  ,page_title  VARCHAR         -- Title of article
  ,link_url    VARCHAR(2083)  -- aka "extlink"
  ,link_desc   VARCHAR
)
;

