import os, sys
from time import strftime
import datetime
from urllib2 import HTTPError

# tornado
from tornado import web

from openmdao.main import __version__
from openmdao.gui.handlers import BaseHandler
from openmdao.gui.projectdb import Projects

    
class IndexHandler(BaseHandler):
    ''' get project list
    '''
    @web.authenticated
    def get(self):
            
        pdb = Projects()
        project_list = pdb.list_projects()
        self.render('projdb/project_list.html', 
                     project_list=project_list,
                     version=__version__)

class DeleteHandler(BaseHandler):
    ''' delete a project
    '''
    @web.authenticated
    def post(self, project_id):

        pdb = Projects()
        project = pdb.get(project_id)
        
        if project['filename']:
            filename = os.path.join(self.get_project_dir(), 
                                    str(project['filename']))
            if os.path.exists(filename):
                os.remove(filename)
                
        pdb.remove(project_id)
        self.redirect('/')

    @web.authenticated
    def get(self, project_id):
        self.redirect('/')

class DetailHandler(BaseHandler):
    ''' get/set project details
    '''
    
    @web.authenticated
    def post(self, project_id):

        forms = {}
        for field in ['projectname', 'description', 'version']:
            if field in self.request.arguments.keys():
                forms[field] = self.request.arguments[field][0]
                
        pdb = Projects()
        
        # Existing project.
        if int(project_id) != pdb.predict_next_rowid():
            project = pdb.get(project_id)
            project_is_new = False
        # New project
        else:
            project = {}
            project['active'] = 0
            project['filename'] = None
            project_is_new = True
        
        if 'projectname' not in forms or \
           len(forms['projectname']) == 0:
            project['projectname'] = "Unnamed Project"
        else:
            project['projectname'] = forms['projectname'].strip()
            
        if 'description' in forms:
            project['description'] = forms['description'].strip()
        else:
            project['description'] =  ''
            
        if 'version' in forms:
            project['version'] = forms['version'].strip()
        else:
            project['version'] =  ''
        
        # if there's no proj file yet, create en empty one
        if not project['filename']:
            
            version = project['version']
            pname = project['projectname']
            
            if len(version):
                filename = '%s-%s.proj' % (pname, version)
            else:
                filename = '%s.proj' % pname
            filename = filename.replace(' ', '_')
            
            unique = filename
            i = 1
            while os.path.exists(os.path.join(self.get_project_dir(), 
                                              unique)):
                unique = filename + '_' + str(i)
                i = i+1
                
            with open(os.path.join(self.get_project_dir(), unique), 'w') as out:
                out.write('')
                out.close()
                
            project['filename'] = unique
            print 'created file:', pname, unique

        if project_is_new:
            pdb.new(project)
        else:
            for key, value in project.iteritems():
                pdb.set(project_id, key, value)
        
        self.redirect(self.request.uri)

    @web.authenticated
    def get(self, project_id):
        
        pdb = Projects()
        project = pdb.get(project_id)
        self.render('projdb/project_detail.html', project=project,
        delete=True)

# FIXME: returns an error even though it works
class DownloadHandler(BaseHandler):
    ''' download a copy of the project
    '''
    @web.authenticated
    def get(self, project_id):
        ''' Browser download of a project file '''
        
        pdb = Projects()
        project = pdb.get(project_id)
        if project['filename']:
            filename = os.path.join(self.get_project_dir(), project['filename'])

            if os.path.exists(filename):
                proj_file = file(filename,'rb')
                self.set_header('content_type', 'application/octet-stream')
                self.set_header('Content-Length', str(os.path.getsize(filename)))
                form_proj = project['projectname'].replace(' ', '_')
                form_ver = project['version'].replace(' ', '_')
                form_date = strftime('%Y-%m-%d_%H%M%S')
                self.set_header('Content-Disposition', 
                                'attachment; filename=%s-%s-%s.proj' % 
                                (form_proj, form_ver, form_date))
                
                try:
                    self.write(proj_file.read())
                finally:
                    proj_file.close()
            else:
                raise HTTPError(filename, 403, "%s is not a file" % filename, 
                                None, None)
        else:
            raise HTTPError(filename, 403, "no file found for %s" % \
                                            project['projectname'], None, None)

class NewHandler(BaseHandler):
    ''' create a new (empty) project
    '''
    @web.authenticated
    def get(self):
        
        pdb = Projects()
        
        project = {}
        project['id'] = pdb.predict_next_rowid()
        project['projectname']   = 'New Project '+strftime("%Y-%m-%d_%H%M%S")
        project['version'] = ''
        project['description'] = ''
        project['modified'] = str(datetime.datetime.now())
        project['filename'] = ''
        project['active'] = ''
        
        self.render('projdb/project_detail.html', project=project, 
                    delete=False)

class AddHandler(BaseHandler):
    ''' upload a file and add it to the project database
    '''
    @web.authenticated
    def post(self):
        
        sourcefile = self.request.files['myfile'][0]
        if sourcefile:
            filename = sourcefile['filename']
            if len(filename) > 0:
                
                pdb = Projects()
                
                # Don't need an extension in the middle of a new name
                if filename[-5:] == '.proj':
                    filename = filename[:-5]
                
                timestring = strftime("%Y-%m-%d_%H%M%S")
                
                project = {}
                project['id'] = pdb.predict_next_rowid()
                project['projectname']   = 'Added_%s_%s' % (filename, 
                                                            timestring)
                project['version'] = ''
                project['description'] = ''
                project['modified'] = str(datetime.datetime.now())
                project['active'] = 1

                unique = filename
                i = 1
                while os.path.exists(os.path.join(self.get_project_dir(), \
                                                  unique)):
                    unique = filename + '_' + str(i)
                    i = i+1
                    
                with open(os.path.join(self.get_project_dir(), 
                                       unique), 'w') as out:
                    out.write(sourcefile['body'])
                    out.close()
                    
                project['filename'] = unique
                pdb.new(project)
                
                self.redirect('/projects/'+str(project['id']))
                
        self.redirect('')

    @web.authenticated
    def get(self):
        self.render('projdb/add_project.html')

handlers = [            
    web.url(r'/projects/?',                              IndexHandler),
    web.url(r'/projects/(?P<project_id>\d+)/?',          DetailHandler),
    web.url(r'/projects/new/$',                          NewHandler),
    web.url(r'/projects/add/$',                          AddHandler),
    web.url(r'/projects/delete/(?P<project_id>\d+)/?',   DeleteHandler),
    web.url(r'/projects/download/(?P<project_id>\d+)/?', DownloadHandler),
]
