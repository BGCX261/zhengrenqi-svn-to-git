package com.zhengrenqi.explorerfile.actions;

import java.io.IOException;
import java.lang.reflect.Method;
import java.util.HashSet;
import java.util.Set;

import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.IResource;
import org.eclipse.core.runtime.IAdaptable;
import org.eclipse.core.runtime.ILog;
import org.eclipse.core.runtime.IPath;
import org.eclipse.core.runtime.Status;
import org.eclipse.jdt.core.IJavaElement;
import org.eclipse.jface.action.IAction;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.jface.viewers.ISelection;
import org.eclipse.jface.viewers.TreePath;
import org.eclipse.jface.viewers.TreeSelection;
import org.eclipse.ui.IEditorInput;
import org.eclipse.ui.IEditorPart;
import org.eclipse.ui.IWorkbenchPart;
import org.eclipse.ui.IWorkbenchWindow;
import org.eclipse.ui.IWorkbenchWindowActionDelegate;

import com.zhengrenqi.explorerfile.Activator;

/**
 * Our sample action implements workbench action delegate. The action proxy will
 * be created by the workbench and shown in the UI. When the user tries to use
 * the action, this delegate will be created and execution will be delegated to
 * it.
 * 
 * @see IWorkbenchWindowActionDelegate
 */
public class ExplorerAction implements IWorkbenchWindowActionDelegate {
	private IWorkbenchWindow window;
	private ILog logger = Activator.getDefault().getLog();
	private ISelection currentSelection;
	public static final String WINDOWS = "win32";
	public static final String LINUX = "linux";
	private String systemBrowser = "explorer";
	private OsType osType = OsType.WINDOWS;

	public enum OsType {
		WINDOWS, LINUX
	}

	/**
	 * 
	 * The constructor.
	 * 
	 */
	public ExplorerAction() {

	}

	/**
	 * The action has been activated. The argument of the method represents the
	 * 'real' action sitting in the workbench UI.
	 * 
	 * @see IWorkbenchWindowActionDelegate#run
	 */
	public void run(IAction action) {
		// String message = "currentSelection is " + currentSelection
		// + "and the class is " + currentSelection.getClass();
		// logger.log(new Status(Status.OK, Activator.PLUGIN_ID, Status.OK,
		// message, null));
		// if ((currentSelection == null)
		// || !(currentSelection instanceof TreeSelection)) return;
		Set<IPath> paths = new HashSet<IPath>();
		if (currentSelection != null)
			getPaths(paths, currentSelection);
		getPaths(paths, window.getActivePage().getActivePart());

		for (IPath path : paths) {
			handlePath(path);
		}
	}

	private void handlePath(IPath path) {
		String location = path.toOSString();
		switch (osType) {
		case WINDOWS: {
			if (path.toFile().isFile()) {
				// location = ((IFile)
				// resource).getParent().getLocation().toOSString();
				location = "/SELECT,\"" + location + "\"";
			}
			String systemBrowser = "explorer";
			try {
				Runtime.getRuntime().exec(systemBrowser + " " + location);
			} catch (IOException e) {
				MessageDialog.openError(window.getShell(), "OpenExploer Error",
						"Can't open " + location);
				e.printStackTrace();
			}
		}

			break;
		case LINUX: {
			String systemBrowser = "nautilus";
			if (path.toFile().isFile()) {
				location = path.toOSString();
			}

			try {
				Runtime.getRuntime().exec(systemBrowser + " " + location);
			} catch (IOException e) {
				MessageDialog.openError(window.getShell(), "OpenExploer Error",
						"Can't open " + location);
				e.printStackTrace();
			}

		}

		default:
			break;
		}
	}

	private void getPaths(Set<IPath> paths, IWorkbenchPart workbenchPart) {
		if (workbenchPart instanceof IEditorPart) {
			IEditorPart editorPart = (IEditorPart) workbenchPart;
			IEditorInput editorInput = editorPart.getEditorInput();
			Object adapterResource = editorInput.getAdapter(IResource.class);

			// Object input= JavaUI.getEditorInputJavaElement(editorInput);
			if (adapterResource instanceof IResource) {
				paths.add(((IResource) adapterResource).getLocation());
				return;
			}
			Object adapterPath = editorInput.getAdapter(IPath.class);
			if (adapterPath instanceof IPath) {
				paths.add((IPath) adapterPath);
				return;
			}

			IJavaElement javaElement = (IJavaElement) editorInput
					.getAdapter(IJavaElement.class);
			IPath path = getPath(javaElement);
			if (path != null) {
				paths.add(path);
				return;
			}
			path = getPath(editorInput);
			paths.add(path);
		}
	}

	private void getPaths(Set<IPath> paths, ISelection selection) {
		if (currentSelection instanceof TreeSelection) {
			TreeSelection treeSelection = (TreeSelection) currentSelection;
			Object element = ((TreeSelection) currentSelection)
					.getFirstElement();
			TreePath[] treePaths = treeSelection.getPaths();

			for (int i = 0; i < treePaths.length; ++i) {
				TreePath treePath = treePaths[i];
				Object segment = treePath.getLastSegment();
				IPath path = getPath(segment);

				if (path != null) {
					paths.add(path);
				}

			}
		}
	}

	private IPath getPath(Object segment) {
		if (segment instanceof IResource)
			return ((IResource) segment).getLocation();

		if (segment instanceof IAdaptable) {
			IAdaptable adaptable = (IAdaptable) segment;
			Object adapterResource = adaptable.getAdapter(IResource.class);
			Object adapterPath = adaptable.getAdapter(IPath.class);
			if (adapterResource instanceof IResource) {
				return ((IResource) adapterResource).getLocation();
			}
		}

		Class clazz = segment.getClass();
		try {
			Method method = clazz.getMethod("getResource", new Class[] {});
			return ((IResource) method.invoke(segment, new Object[] {}))
					.getLocation();
		} catch (Exception e) {
			// logger.log(new Status(Status.ERROR, Activator.PLUGIN_ID,
			// Status.OK,
			// e.getMessage(), e));
		}
		try {
			Method method = clazz.getMethod("getPath", new Class[] {});
			return (IPath) method.invoke(segment, new Object[] {});
		} catch (Exception e) {
			// logger.log(new Status(Status.ERROR, Activator.PLUGIN_ID,
			// Status.OK,
			// e.getMessage(), e));
		}
		return null;
	}

	private void handleResource(IResource resource) {
		String location = resource.getLocation().toOSString();
		switch (osType) {
		case WINDOWS: {
			if (resource instanceof IFile) {
				// location = ((IFile)
				// resource).getParent().getLocation().toOSString();
				location = "/SELECT,\"" + location + "\"";
			}
			String systemBrowser = "explorer";
			try {
				Runtime.getRuntime().exec(systemBrowser + " " + location);
			} catch (IOException e) {
				MessageDialog.openError(window.getShell(), "OpenExploer Error",
						"Can't open " + location);
				e.printStackTrace();
			}
		}

			break;
		case LINUX: {
			String systemBrowser = "nautilus";
			if (resource instanceof IFile) {
				location = ((IFile) resource).getParent().getLocation()
						.toOSString();
			}

			try {
				Runtime.getRuntime().exec(systemBrowser + " " + location);
			} catch (IOException e) {
				MessageDialog.openError(window.getShell(), "OpenExploer Error",
						"Can't open " + location);
				e.printStackTrace();
			}

		}

		default:
			break;
		}

	}

	private void getResources(Set<IResource> resources,
			IWorkbenchPart workbenchPart) {

	}

	private void getResources(Set<IResource> resources, ISelection selection) {
		if (currentSelection instanceof TreeSelection) {
			TreeSelection treeSelection = (TreeSelection) currentSelection;
			Object element = ((TreeSelection) currentSelection)
					.getFirstElement();
			TreePath[] paths = treeSelection.getPaths();

			for (int i = 0; i < paths.length; ++i) {
				TreePath path = paths[i];
				Object segment = path.getLastSegment();
				IResource resource = getResource(segment);

				if (resource != null) {
					resources.add(resource);
				}

			}
		}
	}

	public IResource getResource(Object segment) {
		if (segment instanceof IResource)
			return (IResource) segment;

		if (segment instanceof IAdaptable) {
			IAdaptable adaptable = (IAdaptable) segment;
			Object adapterObject = adaptable.getAdapter(IResource.class);
			if (adapterObject instanceof IResource) {
				return (IResource) adapterObject;
			}
		}

		try {
			Class clazz = segment.getClass();
			Method method = clazz.getMethod("getResource", new Class[] {});
			return (IResource) method.invoke(segment, new Object[] {});
		} catch (Exception e) {
			logger.log(new Status(Status.ERROR, Activator.PLUGIN_ID, Status.OK,
					e.getMessage(), e));
		}
		return null;
	}

	private void printClass(Class clazz) {
		if (clazz == null) {
			return;
		}
		Class[] Interfaces = clazz.getInterfaces();
		for (Class Interface : Interfaces) {
			printClass(Interface);
		}
		printClass(clazz.getSuperclass());
		System.out.println(clazz);
	}

	/**
	 * Selection in the workbench has been changed. We can change the state of
	 * the 'real' action here if we want, but this can only happen after the
	 * delegate has been created.
	 * 
	 * @see IWorkbenchWindowActionDelegate#selectionChanged
	 */
	public void selectionChanged(IAction action, ISelection selection) {
		this.currentSelection = selection;
	}

	/**
	 * We can use this method to dispose of any system resources we previously
	 * allocated.
	 * 
	 * @see IWorkbenchWindowActionDelegate#dispose
	 */
	public void dispose() {
		// window.getSelectionService().removeSelectionListener(this);
	}

	/**
	 * We will cache window object in order to be able to provide parent shell
	 * for the message dialog.
	 * 
	 * @see IWorkbenchWindowActionDelegate#init
	 */
	public void init(IWorkbenchWindow window) {
		this.window = window;
		// window.getSelectionService().addSelectionListener(this);
		// systemBrowser = "explorer";
		// systemBrowser = "nautilus";
		String os = System.getProperty("osgi.os");
		if (WINDOWS.equalsIgnoreCase(os))
			osType = OsType.WINDOWS;
		else if (LINUX.equalsIgnoreCase(os))
			osType = OsType.LINUX;
	}

}
