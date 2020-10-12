DROP TABLE IF EXISTS public.station_status_history;

CREATE TABLE IF NOT EXISTS public.station_status_history
(
	station_id INT
	,num_bikes_available INT
	,is_installed BOOLEAN
	,is_returning BOOLEAN
	,is_renting BOOLEAN
	,last_reported TIMESTAMP
	,load_partition VARCHAR(10)
	,PRIMARY KEY(station_id, last_reported)
)
DISTKEY(station_id)
SORTKEY(last_reported);

DROP TABLE IF EXISTS public.station_review_sentiment;

CREATE TABLE IF NOT EXISTS public.station_review_sentiment
(
	station_id INT
	,user_id VARCHAR(64)
	,review VARCHAR(255)
	,sentiment VARCHAR(16)
	,sentiment_mixed FLOAT
	,sentiment_neutral FLOAT
	,sentiment_positive FLOAT
	,sentiment_negative FLOAT
	,create_date TIMESTAMP
	,load_partition VARCHAR(10)
	,PRIMARY KEY(station_id, user_id, create_date)
)
DISTKEY(station_id)
SORTKEY(create_date);

DROP TABLE IF EXISTS public.station_detail;

CREATE TABLE IF NOT EXISTS public.station_detail
(
	station_id INT
	,station_name VARCHAR(128)
	,capacity INT
	,lon FLOAT
	,lat FLOAT
	,last_updated TIMESTAMP
	,PRIMARY KEY(station_id)
)