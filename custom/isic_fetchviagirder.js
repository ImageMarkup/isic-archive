

isbi_date_set_names = [ {'FolderName': 'ISBI2016_ISIC_Part1_Training_Data' ,'FolderDesc':'ISBI2016_ISIC_Part1_Training_Data' }]

girder_base_url = 'https://girder.neuro.emory.edu:443/api/v1/'

p1Folder = {};
p1FolderItems = {};


//https://girder.neuro.emory.edu/?#item/57003cdcb0e9576a6beb536c
function girder_getFolderByName( FolderName )
	{

		gfb_url = girder_base_url + 'folder?text='+FolderName + '&limit=50&offset=0&sort=name&sortdir=1'
		console.log(gfb_url);
		$.getJSON(gfb_url).success( function(result) { console.log(result);  p1Folder = result; });
	
		//To make things easier, I am storing the collection name so I need to do this get the UID
	}


function girder_getFolderContentsById ( folderID )
	{


		//https://girder.neuro.emory.edu:443/api/v1/item?folderId=56ff1158b0e9576a6beb48d8&limit=0&offset=0&sort=lowerName&sortdir=1
		item_limit = 0; //Eventually want to paginate this

		gfcbyId_url = girder_base_url + 'item?folderId=' + folderID + '&limit=' +item_limit + '&offset=0&'
		console.log(gfcbyId_url);
		$.getJSON(gfcbyId_url).success( function(result) { console.log(result); p1FolderItems=result;   });
	
		//To make things easier, I am storing the collection name so I need to do this get the UID
	}

function girder_getItemFiles ( itemID )
	{
		//This will get the items in a specific folder

		//https://girder.neuro.emory.edu:443/api/v1/item?folderId=56ff1158b0e9576a6beb48d8&limit=0&offset=0&sort=lowerName&sortdir=1
		item_limit = 0; //Eventually want to pagina

		//'https://girder.neuro.emory.edu:443/api/v1/item/57003cdcb0e9576a6beb536c/files?limit=50&offset=0&sort=name&sortdir=1'

		getItemFiles_url = girder_base_url + 'item/'+itemID + '/files?&limit=' +item_limit + '&offset=0&sort=name'
		console.log(getItemFiles_url);
		$.getJSON(getItemFiles_url).success( function(result) { console.log(result); p1FolderItems=result;   });
	
		//To make things easier, I am storing the collection name so I need to do this get the UID
	}
//So an item can also have a set of files associated with it, which do not create a folder directly...
//This synta can get a bit confusing.

//https://girder.neuro.emory.edu:443/api/v1/item/57003cdcb0e9576a6beb536c/files?limit=0&offset=0&sort=name&sortdir=1

//getFilesForanItem
//57003cdcb0e9576a6beb536c  Phase 1 JPEG images are in this directory...




