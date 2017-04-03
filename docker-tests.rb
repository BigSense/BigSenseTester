#!/usr/bin/env ruby

require 'docker'
require 'logger'

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

def container_config
  {
   'mysql' => {
     'type' => 'docker',
     'image' => 'mysql/mysql-server:5.7',
     'container_args' => {
       'Env' => [
         'MYSQL_ROOT_PASSWORD=testroot',
         'MYSQL_DATABASE=BigSense',
         'MYSQL_USER=bigsense',
         'MYSQL_PASSWORD=bigsense'
       ],
       'ExposedPorts' => {'3306/tcp' => {}},
       'HostConfig' => {
         'PortBindings' => {
          '3306/tcp' => [{ 'HostPort' => '3306' }]
         }
       }
     }
   },
   'postgres' => {
     'type' => 'docker',
     'image_args' => {
       'dockerfile' => 'BigSensePostgres'
     },
     'container_args' => {
       'Env' => [
         'POSTGRES_DB=bigsense',
         'POSTGRES_USER=bigsense_ddl',
         'POSTGRES_PASSWORD=bigsense_ddl'
       ],
       'ExposedPorts' => {'5432/tcp' => {}},
       'HostConfig' => {
         'PortBindings' => {
          '5432/tcp' => [{ 'HostPort' => '5432' }]
         }
       }
     }
   },
   'mssql' => {
     'type' => 'docker',
     'image' => 'microsoft/mssql-server-linux',
     'container_args' => {
       'Env' => [
         'ACCEPT_EULA=Y',
         'SA_PASSWORD=B1gS3ns301'
       ],
      'ExposedPorts' => {'1433/tcp' => {}},
      'HostConfig' => {
        'PortBindings' => {
         '1433/tcp' => [{ 'HostPort' => '1433' }]
        }
      }
     }
   },
   'mssql-client' => {
     'type' => 'docker',
     'image_args' => {
       'dockerfile' => 'MsSqlClient'
     },
     'container_args' => {
       'Env' => [
         'DATABASE=BigSense',
         'SA_PASSWORD=B1gS3ns301',
         'DATABASE=BigSense',
         'DB_USER=bigsense',
         'DB_PASS=B1gs3nse400'
       ],
       'HostConfig' => {
         'Links' => ["bigsense-mssql"]
       }
     }
   },
   'tomcat-mysql' => {
     'type' => 'docker',
     'image' => 'bigsense.io/bigsense',
     'container_args' => {
       'Env' => [
         "DBMS=mysql",
         "DB_HOSTNAME=bigsense-mysql",
         "DB_DATABASE=BigSense",
         "DB_PORT=3306",
         "DB_USER=bigsense",
         "DB_PASS=bigsense",
         "DBO_USER=root",
         "DBO_PASS=testroot",
         "SECURITY_MANAGER=Disabled",
         "SERVER=tomcat",
         "HTTP_PORT=9090"
       ],
       'ExposedPorts' => {'9090/tcp' => {}},
       'HostConfig' => {
         'Links' => ["bigsense-mysql"],
         'PortBindings' => {
          '9090/tcp' => [{ 'HostPort' => '9090' }]
         }
       }
     }
   },
   'tomcat-postgres' => {
     'type' => 'docker',
     'image' => 'bigsense.io/bigsense',
     'container_args' => {
       'Env' => [
         "DBMS=pgsql",
         "DB_HOSTNAME=bigsense-postgres",
         "DB_DATABASE=bigsense",
         "DB_PORT=5432",
         "DB_USER=bigsense",
         "DB_PASS=bigsense",
         "DBO_USER=bigsense_ddl",
         "DBO_PASS=bigsense_ddl",
         "SECURITY_MANAGER=Disabled",
         "SERVER=tomcat",
         "HTTP_PORT=9091"
       ],
       'ExposedPorts' => {'9091/tcp' => {}},
       'HostConfig' => {
         'Links' => ["bigsense-postgres"],
         'PortBindings' => {
          '9091/tcp' => [{ 'HostPort' => '9091' }]
         }
       }
     }
   },
   'tomcat-mssql' => {
     'type' => 'docker',
     'image' => 'bigsense.io/bigsense',
     'container_args' => {
       'Env' => [
         "DBMS=mssql",
         "DB_HOSTNAME=bigsense-mssql",
         "DB_DATABASE=bigsense",
         "DB_PORT=1433",
         "DB_USER=bigsense",
         "DB_PASS=bigsense",
         "DBO_USER=bigsense_ddl",
         "DBO_PASS=bigsense_ddl",
         "SECURITY_MANAGER=Disabled",
         "SERVER=tomcat",
         "HTTP_PORT=9091"
       ],
       'ExposedPorts' => {'9092/tcp' => {}},
       'HostConfig' => {
         'Links' => ["bigsense-mssql"],
         'PortBindings' => {
          '9092/tcp' => [{ 'HostPort' => '9092' }]
         }
       }
     }
   }
  }
end

def existing_containers
  enum_for(:sense_containers).to_a
end

#def find_container(name)
#  existing_containers.find { |c| c.info['Names'].any? { |n| } }
#end

def create_containers
  container_config.map { |name, params|
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
create_containers()
