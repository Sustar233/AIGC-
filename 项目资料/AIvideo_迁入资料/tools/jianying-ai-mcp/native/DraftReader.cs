// Local C# port of native/jy_draft_crypto.cpp (MIT, wenshui330 / upstream attribution retained).
// Reads only the input supplied by the MCP client; writes a separate JSON output.
using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
class DraftReader {
 [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern IntPtr LoadLibraryEx(string n, IntPtr h,uint flags);
 [DllImport("kernel32.dll", CharSet=CharSet.Ansi, SetLastError=true)] static extern IntPtr GetProcAddress(IntPtr h,string n);
 [DllImport("kernel32.dll", CharSet=CharSet.Unicode)] static extern IntPtr AddDllDirectory(string p);
 [DllImport("kernel32.dll")] static extern uint SetErrorMode(uint mode);
 [UnmanagedFunctionPointer(CallingConvention.Cdecl)] delegate IntPtr Decrypt(IntPtr self,IntPtr output,IntPtr input,IntPtr parms,IntPtr ok);
 static IntPtr MakeString(byte[] data){
   IntPtr s=Marshal.AllocHGlobal(32); Marshal.Copy(new byte[32],0,s,32);
   if(data.Length<16) { Marshal.Copy(data,0,s,data.Length); Marshal.WriteInt64(s,24,15); }
   else { IntPtr b=Marshal.AllocHGlobal(data.Length+1); Marshal.Copy(data,0,b,data.Length);Marshal.WriteByte(b,data.Length,0);Marshal.WriteIntPtr(s,b);Marshal.WriteInt64(s,24,data.Length); }
   Marshal.WriteInt64(s,16,data.Length);return s;
 }
 static int Main(string[] args){
  try{
   if(args.Length!=5||args[0]!="--decrypt"||args[3]!="--install-dir") throw new Exception("usage: --decrypt input output --install-dir path");
   string input=Path.GetFullPath(args[1]),output=Path.GetFullPath(args[2]),install=Path.GetFullPath(args[4]);
   if(String.Equals(input,output,StringComparison.OrdinalIgnoreCase))throw new Exception("Input and output must differ");
   SetErrorMode(0x8001); AddDllDirectory(install);
   Environment.SetEnvironmentVariable("PATH",install+";"+Environment.GetEnvironmentVariable("PATH"));
   Directory.SetCurrentDirectory(install);
   IntPtr lib=LoadLibraryEx(Path.Combine(install,"videoeditor.dll"),IntPtr.Zero,0x100|0x200|0x800|0x400);
   if(lib==IntPtr.Zero)throw new Exception("LoadLibrary error "+Marshal.GetLastWin32Error());
   IntPtr fn=GetProcAddress(lib,"?decrypt@EncryptUtils@lvve@@QEAA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@AEBV34@0AEA_N@Z");
   if(fn==IntPtr.Zero)throw new Exception("Decrypt export unavailable");
   Decrypt dec=(Decrypt)Marshal.GetDelegateForFunctionPointer(fn,typeof(Decrypt));
   IntPtr source=MakeString(File.ReadAllBytes(input)),parms=MakeString(Encoding.UTF8.GetBytes("{}")),result=MakeString(new byte[0]),ok=Marshal.AllocHGlobal(1);
   Marshal.WriteByte(ok,0);dec(IntPtr.Zero,result,source,parms,ok);
   long length=Marshal.ReadInt64(result,16),cap=Marshal.ReadInt64(result,24);
   if(Marshal.ReadByte(ok)==0||length<=0||length>200000000)throw new Exception("Decrypt returned no valid content");
   byte[] bytes=new byte[(int)length];Marshal.Copy(cap<16?result:Marshal.ReadIntPtr(result),bytes,0,bytes.Length);
   File.WriteAllBytes(output,bytes);Console.WriteLine("ok");return 0;
  }catch(Exception e){Console.Error.WriteLine(e.Message);return 1;}
 }
}

