#!/usr/bin/env ruby

require 'docker'
require 'logger'
require 'socket'
require 'optparse'

class String
def red;            "\033[91m#{self}\033[0m" end
def green;          "\033[92m#{self}\033[0m" end
def blue;           "\033[94m#{self}\033[0m" end
def magenta;        "\033[95m#{self}\033[0m" end
end

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

def wait_for_service(container, port)
  launch_containers(
    create_container('client-wait', nil, 'PortWait', nil,
      ["HOST=bigsense-#{container}", "PORT=#{port}"],
      [container]),
      true)
end

def create_container(name, image, dockerfile, port, env, link)
  {
   name => {
     'image' => image,
     'image_args' => ({
       'dockerfile' => dockerfile
     } if not dockerfile.nil?),
     'container_args' => {
       'Env' => env,
       'ExposedPorts' => ({"#{port}/tcp" => {}} if not port.nil?),
       'HostConfig' => {
         'Links' => (link.map{ |l| "bigsense-#{l}" } if not link.nil?),
         'PortBindings' => ({
           "#{port}/tcp" => [{ 'HostPort' => port }]
         } if not port.nil?)
       }.reject{ |k,v| v.nil? }
     }
   }.reject{ |k,v| v.nil? }
 }
end

def db_containers()
  create_container('db-mysql', 'mysql:5', nil, '3306', [
    'MYSQL_ROOT_PASSWORD=testroot', 'MYSQL_DATABASE=bigsense', 'MYSQL_USER=bigsense', 'MYSQL_PASSWORD=bigsense'
  ], nil).merge(
  create_container('db-postgres', nil, 'BigSensePostgres', '5432', [
    'POSTGRES_DB=bigsense', 'POSTGRES_USER=bigsense_ddl', 'POSTGRES_PASSWORD=bigsense_ddl'
  ], nil).merge(
  create_container('db-mssql', 'microsoft/mssql-server-linux', nil, '1433', [
    'ACCEPT_EULA=Y', 'SA_PASSWORD=B1gS3ns301'
  ], nil).merge(
  create_container('client-mssql', nil, 'MsSqlClient', nil, [
    'DATABASE=bigsense', 'SA_PASSWORD=B1gS3ns301', 'DB_USER=bigsense_ddl',
    'DB_PASSWORD=bigsense_ddl'
  ], ['db-mssql'])
  )))
end

def bs_containers()
  create_container('tomcat-mysql', 'bigsense.io/bigsense', nil, '9090', [
    "DBMS=mysql", "DB_HOSTNAME=bigsense-db-mysql", "DB_DATABASE=bigsense", "DB_PORT=3306",
    "DB_USER=bigsense", "DB_PASS=bigsense", "DBO_USER=root", "DBO_PASS=testroot",
    "SECURITY_MANAGER=Signature", "SERVER=tomcat", "HTTP_PORT=9090"
  ], ['db-mysql']).merge(
  create_container('tomcat-postgres', 'bigsense.io/bigsense', nil, '9091',  [
    "DBMS=pgsql", "DB_HOSTNAME=bigsense-db-postgres", "DB_DATABASE=bigsense", "DB_PORT=5432",
    "DB_USER=bigsense", "DB_PASS=bigsense", "DBO_USER=bigsense_ddl", "DBO_PASS=bigsense_ddl",
    "SECURITY_MANAGER=Signature", "SERVER=tomcat", "HTTP_PORT=9091"
  ], ['db-postgres']).merge(
  create_container('tomcat-mssql', 'bigsense.io/bigsense', nil, '9092',  [
    "DBMS=mssql", "DB_HOSTNAME=bigsense-db-mssql", "DB_DATABASE=bigsense", "DB_PORT=1433",
    "DB_USER=bigsense", "DB_PASS=bigsense", "DBO_USER=SA", "DBO_PASS=B1gS3ns301",
    "SECURITY_MANAGER=Signature", "SERVER=tomcat", "HTTP_PORT=9092"
  ], ['db-mssql'])
  ))
end

def fixtures_container()
  create_container('client-fixtures', nil, 'SQLFixtures', nil,  [],
    ['db-mssql', 'db-postgres', 'db-mysql'])
end

def existing_containers
  enum_for(:sense_containers).to_a
end

#def find_container(name)
#  existing_containers.find { |c| c.info['Names'].any? { |n| } }
#end

def launch_containers(containers, wait = false)
  containers.map { |name, params|
    # for all bigsense containers that don't exist yet
    if not existing_containers.any? { |e| e.info['Names'].any? { |n| n.split('-')[1] == name } }
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
      c = Docker::Container.create(
        {
          'Image' => image,
        'name' => 'bigsense-%s' %[name]
        }.merge(params['container_args'])
      )
      c.start()
      $log.info('bigsense-%s container started' %[name])
      if wait
        $log.info('Waiting for bigsense-%s to complete' %[name])
        c.wait()
        $log.info('bigsense-%s finished' %[name])
        c.delete(:force => true)
      end
    end
  }
end

def print_results(results)
  puts("\n\nIntegration Test Results".blue)
  puts("--------------------------------\n")
  results.map { |name,result|
    out = '['.blue + (result ? "  ok  ".green : " fail ".red) + ']'.blue
    puts('%-25s %s' %["#{name} Tests:".magenta, out])
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

options = {}
OptionParser.new do |opts|
  opts.banner = "Usage: docker-tests.rb [-r] [-b] [-t]"

  opts.on("-r", "--rebuild", "Rebuild Entire Docker Environment") do |r|
    options[:rebuild] = r
  end

  opts.on("-b", "--bigsense", "Rebuild BigSense Containers") do |bs|
    options[:build_bigsense] = bs
  end

  opts.on("-t", "--tests", "Run Big Sense Tests") do |tests|
    options[:tests] = tests
  end

end.parse!

if options[:rebuild]
  clean_containers()
  launch_containers(db_containers)
  wait_for_service('db-mysql', 3306)
  wait_for_service('db-postgres', 5432)
  wait_for_service('db-mssql', 1433)
  launch_containers(bs_containers)
  wait_for_service('tomcat-mysql', 9090)
  wait_for_service('tomcat-postgres', 9091)
  wait_for_service('tomcat-mssql', 9092)
  launch_containers(fixtures_container, true)
end

if options[:tests]
  print_results(
    {
      "MySQL" => system('./bst.py BigSenseMasterTestSet -s localhost -p 9090'),
      "Postgres" => system('./bst.py BigSenseMasterTestSet -s localhost -p 9091'),
      "MS SQL" => system('./bst.py BigSenseMasterTestSet -s localhost -p 9092')
    }
  )
end
