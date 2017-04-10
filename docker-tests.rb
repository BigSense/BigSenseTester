#!/usr/bin/env ruby

require 'docker'
require 'logger'
require 'socket'

$log = Logger.new(STDOUT)

def sense_containers
  Docker::Container.all(:all => true).each { |c|
    c.info['Names'].each { |name|
      if(name.start_with?('/bigsense'))
        unit = name.split('-')[1]
        if(unit)
          yield c
        end
      end
    }
  }
end

def wait_for_service(port)
  begin
    Timeout::timeout(5) do
      begin
        s = TCPSocket.new('localhost', port)
        s.close
        $log.info("Service accepting connections on #{port}")
        return true
      rescue Errno::ECONNREFUSED, Errno::EHOSTUNREACH
        sleep(2)
        retry
      end
    end
  rescue Timeout::Error
    $log.info("Service not ready on #{port}. Retrying...")
    return false
  end
end

def create_container(name, image, dockerfile, port, env, link)
  {
   name => {
     'type' => 'docker',
     'image' => image,
     'image_args' => ({
       'dockerfile' => dockerfile
     } if not dockerfile.nil?),
     'container_args' => {
       'Env' => env,
       'ExposedPorts' => ({"#{port}/tcp" => {}} if not port.nil?),
       'HostConfig' => {
         'Links' => (["bigsense-#{link}"] if not link.nil?),
         'PortBindings' => ({
           "#{port}/tcp" => [{ 'HostPort' => port }]
         } if not port.nil?)
       }.reject{ |k,v| v.nil? }
     }
   }.reject{ |k,v| v.nil? }
 }
end

def db_containers()
  create_container('db-mysql', 'mysql/mysql-server:5.7', nil, '3306', [
    'MYSQL_ROOT_PASSWORD=testroot', 'MYSQL_DATABASE=BigSense', 'MYSQL_USER=bigsense', 'MYSQL_PASSWORD=bigsense'
  ], nil).merge(
  create_container('db-postgres', nil, 'BigSensePostgres', '5432', [
    'POSTGRES_DB=bigsense', 'POSTGRES_USER=bigsense_ddl', 'POSTGRES_PASSWORD=bigsense_ddl'
  ], nil).merge(
  create_container('db-mssql', 'microsoft/mssql-server-linux', nil, '1433', [
    'ACCEPT_EULA=Y', 'SA_PASSWORD=B1gS3ns301'
  ], nil).merge(
  create_container('client-mssql', nil, 'MsSqlClient', nil, [
    'DATABASE=BigSense', 'SA_PASSWORD=B1gS3ns301', 'DATABASE=BigSense', 'DB_USER=bigsense_ddl',
    'DB_PASSWORD=bigsense_ddl'
  ], 'db-mssql')
  )))
end

def bs_containers()
  create_container('tomcat-mysql', 'bigsense.io/bigsense', nil, '9090', [
    "DBMS=mysql", "DB_HOSTNAME=bigsense-db-mysql", "DB_DATABASE=BigSense", "DB_PORT=3306",
    "DB_USER=bigsense", "DB_PASS=bigsense", "DBO_USER=root", "DBO_PASS=testroot",
    "SECURITY_MANAGER=Disabled", "SERVER=tomcat", "HTTP_PORT=9090"
  ], 'db-mysql').merge(
  create_container('tomcat-postgres', 'bigsense.io/bigsense', nil, '9091',  [
    "DBMS=pgsql", "DB_HOSTNAME=bigsense-db-postgres", "DB_DATABASE=bigsense", "DB_PORT=5432",
    "DB_USER=bigsense", "DB_PASS=bigsense", "DBO_USER=bigsense_ddl", "DBO_PASS=bigsense_ddl",
    "SECURITY_MANAGER=Disabled", "SERVER=tomcat", "HTTP_PORT=9091"
  ], 'db-postgres').merge(
  create_container('tomcat-mssql', 'bigsense.io/bigsense', nil, '9092',  [
    "DBMS=mssql", "DB_HOSTNAME=bigsense-db-mssql", "DB_DATABASE=bigsense", "DB_PORT=1433",
    "DB_USER=bigsense", "DB_PASS=bigsense", "DBO_USER=SA", "DBO_PASS=B1gS3ns301",
    "SECURITY_MANAGER=Disabled", "SERVER=tomcat", "HTTP_PORT=9092"
  ], 'db-mssql')
  ))
end

def existing_containers
  enum_for(:sense_containers).to_a
end

#def find_container(name)
#  existing_containers.find { |c| c.info['Names'].any? { |n| } }
#end

def create_containers(containers)
  containers.map { |name, params|
    # for all bigsense containers that don't exist yet
    if not existing_containers.any? { |e| e.info['Names'].any? { |n| n.split('-')[1] == name } }
      case params['type']
      when 'docker'
        $log.info('Creating Image for %s' %[name])
        image = case
        when params.key?('image_args')
          Docker::Image.build_from_dir('./dockerfiles', params['image_args']).id
        when params.key?('image')
          params['image']
        else
          $log.error('Missing image key')
        end
        $log.debug('Image Id %s' %[image])
        Docker::Container.create(
          {
            'Image' => image,
          'name' => 'bigsense-%s' %[name]
          }.merge(params['container_args'])
        ).start()
        $log.info('bigsense-%s container started' %[name])
      end
    end
  }
end

def clean_containers
  sense_containers { |c|
    begin
      $log.info('Deleting Container %s' %[c.info['Names']])
      c.delete(:force => true)
    rescue Docker::Error::NotFoundError
      $log.warn('Could not delete container. Container not found.')
    end
  }
end

clean_containers()
create_containers(db_containers)
wait_for_service(3306)
wait_for_service(5432)
wait_for_service(1433)
create_containers(bs_containers)
wait_for_service(9090)
wait_for_service(9091)
wait_for_service(9092)
bs_mysql = system('./bst.py BigSenseMasterTestSet -s localhost -p 9090')
bs_pgsql = system('./bst.py BigSenseMasterTestSet -s localhost -p 9091')
bs_mssql = system('./bst.py BigSenseMasterTestSet -s localhost -p 9092')

puts("MySQL Tests: #{bs_mysql}")
puts("Postgres Tests: #{bs_pgsql}")
puts("MS SQL Tests: #{bs_mssql}")
