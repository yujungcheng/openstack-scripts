#!/usr/bin/env bash
# get delete data count for each table in Nova DB.


# get shadow tables in nova DB
shadow_tables=($(mysql -B -e "use nova; SELECT TABLE_NAME FROM information_schema.tables WHERE table_schema = DATABASE() AND TABLE_ROWS != 0;" | grep "shadow_"))

echo "Check at $(date)"

for shadow_table in ${shadow_tables[@]}; do

  table=$(echo ${shadow_table} | sed 's/shadow_//g')
  deleted_count=$(mysql -sN -e "use nova; select count(*) from ${table} where deleted!=0")
  echo "- ${table}: ${deleted_count} rows deleted"

done

