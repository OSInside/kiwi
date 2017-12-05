<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
        indent="yes" omit-xml-declaration="no" encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="conv66to67">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv66to67"/>
    </xsl:copy>  
</xsl:template>

<!-- version update -->
<!-- remove kiwirevision attribute from image -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>6.6</literal> to <literal>6.7</literal>.
</para>
<xsl:template match="image" mode="conv66to67">
    <xsl:choose>
        <!-- nothing to do if already at 6.7 -->
        <xsl:when test="@schemaversion > 6.6">
            <xsl:copy-of select="/"/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="6.7">
                <xsl:copy-of select="@*[local-name() != 'schemaversion' and local-name() != 'kiwirevision']"/>
                <xsl:apply-templates  mode="conv66to67"/>  
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- delete checkprebuilt and fsnocheck attributes from type -->
<para xmlns="http://docbook.org/ns/docbook">
    Delete checkprebuilt and fsnocheck attributes from type
</para>
<xsl:template match="type" mode="conv66to67">
    <type>
        <xsl:copy-of select="@*[not(local-name(.) = 'checkprebuilt') and not(local-name(.) = 'fsnocheck')]"/>
        <xsl:apply-templates mode="conv66to67"/>
    </type>
</xsl:template>

<!-- delete status and prefer-license attributes from repository -->
<para xmlns="http://docbook.org/ns/docbook">
    Delete status and prefer-license attributes from repository
</para>
<xsl:template match="repository" mode="conv66to67">
    <repository>
        <xsl:copy-of select="@*[not(local-name(.) = 'status') and not(local-name(.) = 'prefer-license')]"/>
        <xsl:apply-templates mode="conv66to67"/>
    </repository>
</xsl:template>

<!-- delete replaces attribute from package -->
<para xmlns="http://docbook.org/ns/docbook">
    Delete replaces attribute from package
</para>
<xsl:template match="package" mode="conv66to67">
    <package>
        <xsl:copy-of select="@*[not(local-name(.) = 'replaces')]"/>
        <xsl:apply-templates mode="conv66to67"/>
    </package>
</xsl:template>

<!-- Delete defaultprebuilt section -->
<para xmlns="http://docbook.org/ns/docbook">
    Delete defaultprebuilt section
</para>
<xsl:template match="defaultprebuilt" mode="conv66to67">
    <xsl:apply-templates select="*" mode="conv66to67"/>
</xsl:template>

<!-- Delete defaultdestination section -->
<para xmlns="http://docbook.org/ns/docbook">
    Delete defaultdestination section
</para>
<xsl:template match="defaultdestination" mode="conv66to67">
    <xsl:apply-templates select="*" mode="conv66to67"/>
</xsl:template>

<!-- Delete defaultroot section -->
<para xmlns="http://docbook.org/ns/docbook">
    Delete defaultroot section
</para>
<xsl:template match="defaultroot" mode="conv66to67">
    <xsl:apply-templates select="*" mode="conv66to67"/>
</xsl:template>

<!-- Delete partitioner section -->
<para xmlns="http://docbook.org/ns/docbook">
    Delete partitioner section
</para>
<xsl:template match="partitioner" mode="conv66to67">
    <xsl:apply-templates select="*" mode="conv66to67"/>
</xsl:template>

<!-- Delete rpm-force section -->
<para xmlns="http://docbook.org/ns/docbook">
    Delete rpm-force section
</para>
<xsl:template match="rpm-force" mode="conv66to67">
    <xsl:apply-templates select="*" mode="conv66to67"/>
</xsl:template>

</xsl:stylesheet>
