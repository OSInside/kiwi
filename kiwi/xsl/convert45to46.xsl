<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
    indent="yes" omit-xml-declaration="no" encoding="utf-8"/>
<xsl:strip-space elements="type"/>

<!-- default rule -->
<xsl:template match="*" mode="conv45to46">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv45to46"/>
    </xsl:copy>  
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>4.5</literal> to <literal>4.6</literal>.
</para>
<xsl:template match="image" mode="conv45to46">
    <xsl:choose>
        <!-- nothing to do if already at 4.6 -->
        <xsl:when test="@schemaversion > 4.5">
            <xsl:copy-of select="/"/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="4.6">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates mode="conv45to46"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- update vmware / vmx -->
<para xmlns="http://docbook.org/ns/docbook"> 
    Change attribute value <tag class="attribute">vmware</tag> to 
    <tag class="attribute">vmx</tag>.
</para>
<xsl:template match="packages[@type='vmware']" mode="conv45to46">
    <packages type="vmx">
                <xsl:copy-of select="@*[not(local-name(.) = 'type')]"/>
        <xsl:apply-templates mode="conv45to46"/>
    </packages>
</xsl:template>

</xsl:stylesheet>
